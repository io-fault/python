"""
# Hash path implementation for compressing file paths.
"""
from collections.abc import Sequence, Iterable
import functools

class FNV(object):
	@classmethod
	def compute(Class, data:bytes):
		c=Class()
		c.update(data)
		return c

	def __init__(self, *, I=0xcbf29ce484222325):
		self.state = I

	def update(self, data:bytes, P=0x100000001b3, I=0xcbf29ce484222325, C=(2**64)-1):
		s = self.state
		for x in data:
			s ^= x
			s *= P
		self.state = s & C

		return self

	def hexdigest(self) -> str:
		return hex(self.state)[2:]

	def digest(self) -> int:
		return int(self.state)

class Segmentation(object):
	"""
	# Hash implementation container providing division logic for constructing
	# the path segment to be used by a resource's key.
	"""

	def __init__(self, implementation, algorithm, depth, length):
		self.implementation = implementation
		self.algorithm = algorithm
		self.depth = depth
		self.length = length

		self.step = self.length // self.depth
		self.edge = self.length + self.step

	@staticmethod
	def divide(digest, length, edge, step) -> Sequence[str]:
		"""
		# Split the hex digest into parts for building a Route to the bucket.
		"""
		return [
			digest[x:y]
			for x, y in zip(
				range(0, length, step),
				range(step, edge, step)
			)
		]

	def __call__(self, key) -> Sequence[str]:
		"""
		# Hash the given key with the configured algorithm returning the divided digest.
		"""

		hi = self.implementation(key)
		digest = hi.hexdigest().lower()

		return self.divide(digest, self.length, self.edge, self.step)

	def identity(self) -> tuple[str, int, int]:
		"""
		# Return a tuple consisting of the algorithm identifier, the number
		# of divisions, and the character length of the hex digest.
		"""
		return (self.algorithm, self.depth, self.length)

	@classmethod
	def from_identity(Class, algorithm='fnv1a_64', depth=2, length=None):
		"""
		# Create an instance using the identity.
		"""
		if algorithm == 'fnv1a_64':
			implementation = FNV.compute
		else:
			# Arguably inefficient, but normally irrelevant.
			import hashlib
			def implementation(k:bytes, *, I=hashlib.__dict__[algorithm]):
				i = I()
				i.update(k)
				return i

		# calculate if not specified.
		if length is None:
			length = len(implementation(b'').hexdigest())
		else:
			length = length

		return Class(implementation, algorithm, depth, length)

class Index(object):
	"""
	# A bucket index for &Directory resources.

	# Manages the sequence of entries for a bucket.

	# The index files are a series of entry identifiers followed
	# by the key on a greater indentation level; the trailing newline
	# of each indentation block not being part of the key.
	"""

	@staticmethod
	def structure(seq, iter=iter, next=next, tab=b'\t'[0]):
		"""
		# Structure the indentation blocks into (key, entry) pairs.
		# The keys are the indented section and the entries are the leading
		# unindented identifier.

		# Trailing newlines *MUST* be present.
		# Structure presumes that the index file was loaded using readlines.

		# Entries (unindented areas) must be a single line followed by one
		# or more indented lines. The initial indentation level (first tab)
		# will be remove; the content will be considered to be the continuation
		# of the key (that's hashed to select this bucket's index).

		# Underscore attributes are representations of stored data.
		"""

		if seq:
			si = iter(seq)
			entry = next(si)
			key = b''

			for x in si:
				if x[0] == tab:
					key += x[1:] # any newlines are part of the key
				else:
					# found unindented block, so start new entry
					yield (key[:-1], entry[:-1])
					entry = x
					key = b''
			else:
				yield (key[:-1], entry[:-1])

	@classmethod
	def from_path(Class, path):
		idx = Class()

		with path.fs_open('rb') as f:
			idx.load(f.readlines())
		return idx

	def __init__(self):
		self.counter = 0
		self._map = {}
		self._state = []

	def load(self, lines):
		"""
		# Load the index from the given line sequence.
		# &lines items *must* have trailing newlines.
		"""

		i = iter(self.structure(lines))
		try:
			counter = next(i)[1]
			self.counter = int(counter.decode('utf-8'))
		except StopIteration:
			self.counter = 0

		# remainder are regular values
		self._state = list(i)
		self._map = dict([(k, v.decode('utf-8')) for k, v in self._state])

	def sequence(self):
		"""
		# Send the serialized index state to the given &write function.
		"""

		yield (str(self.counter).encode('utf-8') + b'\n')
		yield from ((v.encode('utf-8') + b'\n\t' + k + b'\n') for (k, v) in self._map.items())

	def keys(self):
		"""
		# Iterator containing the keys loaded from the index.
		"""
		return self._map.keys()

	def items(self):
		return self._map.items()

	def has_key(self, key):
		"""
		# Check if a key exists in the index.
		"""
		return key in self._map

	def __getitem__(self, key):
		return self._map[key]

	def __delitem__(self, key):
		del self._map[key]

	def allocate(self, keys, filename):
		"""
		# Allocate a sequence of entries for the given keys.
		"""

		return [
			self._map[k] if k in self._map
			else self.insert(k, filename)
			for k in keys
		]

	def insert(self, key, filename):
		"""
		# Insert the key into the bucket. The key *must* not already be present.
		"""
		self.counter = c = self.counter + 1
		r = self._map[key] = filename(c)

		return r

	def delete(self, key):
		"""
		# Delete the key from the index returning the entry for removal.
		"""

		entry = self._map.pop(key)
		return entry

class Directory(object):
	"""
	# Filesystem based hash tree.

	# [ Properties ]

	# /addressing/
		# The address resolution method. Usually a &Segmentation instance.
	# /path/
		# The route to the resource that contains the tree.
	"""
	index_name = '.index'
	addressing: Segmentation
	path: object

	def __init__(self, addressing:Segmentation, directory):
		self.addressing = addressing
		self.path = directory

	def items(self) -> Iterable[(bytes, object)]:
		"""
		# Returns an iterator to all the keys and their associated routes.
		"""

		q = [self.path]
		while q:
			fsdir = q.pop(0)

			dirs = fsdir.fs_list()[0]
			for x in dirs:
				idx_path = x / self.index_name
				if idx_path.fs_type() != 'void':
					yield from (
						(k, (x / v))
						for k, v in self._index(idx_path).items()
					)
				else:
					# container, descend if &x/index does not exist.
					q.append(x)

	@functools.lru_cache(32)
	def _index(self, route):
		idx = Index()

		with route.fs_open('rb') as f:
			idx.load(f.readlines())

		return idx

	def allocate(self, key, *, filename=str) -> object:
		"""
		# Allocate a position for the given &key and return its route.

		# If already allocated, return the reference to the resource.
		"""

		r = self.path + self.addressing(key)
		ir = r / self.index_name
		ir.fs_init()

		# update the index
		idx = self._index(ir)

		entry = idx.allocate((key,), filename=filename)[0]
		with ir.fs_open('wb') as f:
			f.writelines(idx.sequence())

		return (r / entry).fs_mkdir()

	def available(self, key) -> bool:
		"""
		# Whether the resource has not been allocated.

		# &True when &key has *not* been associated with a resource.
		"""

		r = self.path + self.addressing(key)
		ir = r / self.index_name
		if ir.fs_type() == 'void':
			return True

		idx = self._index(ir)
		if idx.has_key(key):
			entry = idx[key]
			er = r / entry
			if er.fs_type() != 'void':
				return False

		return True

	def release(self, key):
		"""
		# Release the allocated resource associated with the &key and delete it from the index.
		"""

		r = self.path + self.addressing(key)
		ir = r / self.index_name
		if ir.fs_type() == 'void':
			return

		# Resolve entry from bucket.
		idx = self._index(ir)
		if not idx.has_key(key):
			return

		# Remove key from index.
		entry = idx[key]
		idx.delete(key)
		with ir.fs_open('wb') as f:
			f.writelines(idx.sequence())

		# Remove allocated directory.
		(r / entry).fs_void()
		return (r / entry)
