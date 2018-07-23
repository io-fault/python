"""
# Range classes for managing associations and sets whose items span ranges.

# [ Engineering ]
# Mapping needs to be implemented.
"""
import operator
import itertools
import typing
import collections
import builtins

def inclusive_range_set(numbers):
	"""
	# Calculate the set of inclusive ranges.

	# Given a iterable of numbers, sort them and create ranges from
	# the contiguous values.

	# [ Parameters ]

	# /numbers
		# Iterable of Integers.
	"""
	l = list(numbers)
	if not l:
		return

	l.sort()
	start = p = None

	for x in l:
		if p is None:
			start = p = x
		elif x - p == 1:
			# adjacent expands range
			p = x
		else:
			# Range broke
			yield IRange((start, p))
			start = p = x
	else:
		yield IRange((start or x, x))

def combine(ranges, len=len, range=builtins.range):
	"""
	# Combine the ranges into a sequence of ranges reducing them according
	# to their overlaps and contiguity. Used by &Set to implement unions.
	"""
	out = []
	rin = list(ranges)
	if not rin:
		# Nothing.
		return out

	cur = rin.pop(0)
	while rin:
		for i in range(len(rin)):
			x = rin[i]
			if cur.continuation(x):
				# joining something, so restart.
				cur = cur.join(x)
				del rin[i]
				break
		else:
			# not a continuation of anything
			out.append(cur)
			cur = rin.pop(0)

	if cur is not None:
		out.append(cur)

	# r[x].start > r[x-1].stop-1
	out.sort()
	return out

class IRange(tuple):
	"""
	# Fully Inclusive range used for cases where the range length always is one or more.
	"""
	__slots__ = ()

	Type:(type) = int

	@property
	def direction(self):
		"""
		# Returns `-1` if the stop is less than the start. `1` if equal or greater than.
		"""
		return 1 if self[0] >= self[1] else -1

	@property
	def start(self):
		"""
		# The beginning of the Range, inclusive.
		"""
		return self[0]

	@property
	def stop(self):
		"""
		# The end of the Range, inclusive.
		"""
		return self[1]

	@classmethod
	def normal(Class, *args):
		"""
		# Create a normal range using the given boundaries; the minimum given will be the
		# start and the maximum will be the stop.
		"""

		return Class((min(*args), max(*args)))

	@classmethod
	def single(Class, index):
		"""
		# Create a range consisting of a single unit.
		"""

		return Class((index, index))

	@classmethod
	def from_string(Class, string):
		if "-" in string:
			return Class.normal(*map(int, string.split('-', 1)))
		else:
			return Class.single(int(string))

	def __contains__(self, x):
		"""
		# Whether or not the range contains the given number.
		"""

		if isinstance(x, self.__class__):
			return self[0] <= x[0] and x[1] <= self[1]
		else:
			return self[0] <= x <= self[1]

	def __str__(self):
		if self[0] == self[1]:
			return str(self[0])
		else:
			return "%s-%s" % self

	def relation(self, r):
		"""
		# The relation of &r with respect to the &self.
		# Returns `-1` if &r is less than the start; `1` if &r is
		# greater than the stop, and `0` if it is contained.

		# ! WARNING:
			# Does not compensate for negative direction ranges.
		"""

		if r < self[0]:
			return -1
		if r > self[1]:
			return 1
		# Contained
		return 0

	def contiguous(self, r, tuple=tuple):
		"""
		# The given range is contiguous with the other, but does *not* &overlaps.
		"""

		tr = tuple(r)
		return self[0]-1 in tr or self[1]+1 in tr

	def overlaps(self, r, min=min, max=max):
		"""
		# The ranges overlap onto each other.
		"""

		low, hi = (min(self,r), max(self,r))
		return low[1] >= hi[0]

	def continuation(self, r):
		"""
		# The ranges are continuous: overlaps or contiguous.
		"""

		low, hi = (min(self,r), max(self,r))
		return low[1]+1 >= hi[0]

	def join(self, r, min=min, max=max):
		"""
		# Combine the ranges regardless of adjacency.
		"""

		return self.normal(min(self[0], r[0]), max(self[1], r[1]))

	def filter(self, ranges:typing.Iterable["IRange"]):
		"""
		# Modify (filter) the &ranges to be outside of &self.
		# If a range is wholly contained, filter it entirely.

		# The filter is a generator and is applied to an iterable of
		# ranges because it is the necessary framework for dropping
		# wholly contained inclusive ranges. Inclusive ranges
		# cannot represent zero length sizes, so it has to drop
		# contained ranges entirely from the generated sequence.

		# [ Parameters ]

		# /ranges
			# Sequence of &IRange instances to be filtered.
		"""

		for x in ranges:
			if x.overlaps(self):
				# adjust x to be outside of self
				if x[1] in self:
					if x[0] in self:
						# wholly contained, filter the range.
						continue
					else:
						# starting point is outside self,
						# but the end point is inside.
						yield self.__class__((x[0], self[0]-1))
				else:
					if x[0] in self:
						# start is in self, but end is outside
						yield self.__class__((self[1]+1, x[1]))
					else:
						# x is around self, but it could span across it.
						if x[0] < self[0] and x[1] > self[1]:
							# spans inside x, so build two ranges
							yield self.__class__((x[0], self[0]-1))
							yield self.__class__((self[1]+1, x[1]))
			else:
				yield x

	def intersect(self, ranges:typing.Iterable["IRange"]) -> typing.Iterable["IRange"]:
		"""
		# Identify the parts of the &ranges that intersect with &self.

		# [ Parameters ]

		# /ranges
			# Sequence of &IRange instances to intersect with &self.

		# [ Returns ]

		# /&*Annotation
			# A iterable producing &IRange instances.
		"""

		for x in ranges:
			x, y = min(self, x), max(self, x)
			if x[1] >= y[0]:
				k = [x[0], x[1], y[0], y[1]]
				k.sort()
				yield self.__class__(k[1:3])

	def exclusive(self):
		"""
		# Return as an exclusive-end range pair.
		"""

		return (self[0], self[1]+1)

	def units(self, step = 1):
		"""
		# Return an iterator to the units in the range.
		"""

		if self.direction > 0:
			return range(self[0], self[1]+1, step)
		else:
			return range(self[0], self[1]-1, -step)

@collections.Set.register
class Set(object):
	"""
	# A set of unique non-contiguous ranges.

	# Implemented using a pair of sequences containing the start and the stop
	# of each range. For sets consisting of single unit ranges, regular &set
	# objects are more efficient. &bisect is used as the search algorithm
	# when checking for containment, so applications requiring high performance
	# may need to convert the range set or portions thereof into a regular &set.
	"""
	from bisect import bisect as _search
	__slots__ = ('starts', 'stops')

	@classmethod
	def from_string(Class, string, separator=' ', tuple=tuple) -> 'Set':
		global combine
		seq = list((IRange.from_string(x) for x in string.split(separator) if x))
		seq.sort()
		reduced = combine(seq)
		return Class(([x[0] for x in reduced], [x[1] for x in reduced]))

	@classmethod
	def from_set(Class, iterable) -> 'Set':
		l = list(inclusive_range_set(iterable))
		return Class.from_normal_sequence(l)

	@classmethod
	def from_normal_sequence(Class, ranges) -> 'Set':
		"""
		# Low-level constructor building a Set from an
		# *ordered sequence* of *non-overlapping* range instances.
		"""
		return Class(([x[0] for x in ranges], [x[1] for x in ranges]))

	def __init__(self, pair):
		st, sp = pair
		self.starts = list(st)
		self.stops = list(sp)

	def __reduce__(self):
		return (self.from_normal_sequence, (list(self),))

	def __iter__(self):
		return map(IRange, zip(self.starts, self.stops))

	def __str__(self):
		return ' '.join(map(str, self))

	def __eq__(self, ns):
		return self.starts == ns.starts and self.stops == ns.stops

	def __len__(self):
		"""
		# Total number of *individual units* held by the set.

		# Working with inclusive ranges, this means that spans from `0` to `100` will
		# have a length of `101`.
		"""

		return sum(x2-x1 for x1, x2 in zip(self.starts, self.stops)) + len(self.starts)

	def intersecting(self, range:IRange, RType=IRange, isinstance=isinstance):
		"""
		# Get the ranges in the set that have intersections with the given range.
		"""
		rstart, rstop = range
		rtype = type(range)
		start = self._search(self.starts, rstart)
		start_position_slice = slice(max(0, start-1), start+1)

		stop = self._search(self.stops, rstop)
		stop_position_slice = slice(max(0, stop-1), stop+1)

		selection = slice(
			start_position_slice.start,
			stop_position_slice.start + stop_position_slice.stop
		)

		ranges = map(rtype, zip(self.starts[selection], self.stops[selection]))

		for x in ranges:
			if rstart in x or rstop in x:
				yield x
			elif x in range:
				yield x

	# &intersecting is used in the following methods
	# in a way that may not be *generally* appropriate.
	# However, considering they are dealing with the
	# case where the query range is one unit in size,
	# the semantics are clearly correct.

	def get(self, item, default=None, RType=IRange):
		rq = RType.single(item)
		for x in self.intersecting(rq):
			return x
		return default

	def __getitem__(self, item, RType=IRange):
		rq = RType.single(item)
		for x in self.intersecting(rq):
			return x
		raise KeyError(item)

	def __contains__(self, item, RType=IRange):
		rq = RType.single(item)
		for i in self.intersecting(rq):
			return True
		else:
			return False

	def add(self, range:IRange, chain=itertools.chain, zip=zip, slice=slice, max=max, map=map):
		"""
		# Add a range to the set combining it with any continuations.
		"""

		start = self._search(self.starts, range[0])
		start_position_slice = slice(max(0, start-1), start+1)

		stop = self._search(self.stops, range[1])
		stop_position_slice = slice(max(0, stop-1), stop+1) # XXX: Likely OB1 bug near here.

		replacement = slice(
			start_position_slice.start,
			stop_position_slice.start + stop_position_slice.stop,
		)

		starti=map(IRange, zip(self.starts[start_position_slice], self.stops[start_position_slice]))
		stopi=map(IRange, zip(self.starts[stop_position_slice], self.stops[stop_position_slice]))
		new_ranges = combine(chain((range,), starti, stopi))

		# Remove anything between.
		self.starts[replacement] = [range.Type(x[0]) for x in new_ranges]
		self.stops[replacement] = [range.Type(x[1]) for x in new_ranges]

	def discard(self, range, slice=slice, map=map, list=list, chain=itertools.chain):
		"""
		# Remove an arbitrary range from the set.
		"""
		start = self._search(self.starts, range[0])
		start_position_slice = slice(max(0, start-1), start+1)

		stop = self._search(self.stops, range[1])
		stop_position_slice = slice(max(0, stop-1), stop+1) # XXX: Likely OB1 bug near here.

		replacement = slice(
			start_position_slice.start,
			stop_position_slice.start + stop_position_slice.stop
		)

		ri = map(IRange, zip(self.starts[replacement], self.stops[replacement]))
		x = list(range.filter(ri))
		if x:
			new_ranges = list(combine(x)) # reduce overlaps.
		else:
			new_ranges = x

		self.starts[replacement] = [range.Type(x[0]) for x in new_ranges]
		self.stops[replacement] = [range.Type(x[1]) for x in new_ranges]

	def intersection(self, range_set, iter=iter, Queue=collections.deque):
		"""
		# Calculate the intersection between two &Set instances.
		# Low-level method. Use (python/operator)`|` for high-level purposes.
		"""

		# self is left side
		i = iter(self)
		q = Queue() # could be a list
		q.append(next(i))

		for x in range_set:
			while q:
				r = q.popleft()

				if r[1] < x[0]:
					# drop r.
					pass
				elif r[0] > x[1]:
					# need to see x exceed r or intersect.
					q.appendleft(r)
					break
				else:
					# Yield any intersections right away,
					# but r still needs to be exceeded by x.
					# So filter the intersections from r,
					# and reprocess it with the purpose of
					# filtering any ranges below x[0]

					ix = tuple(x.intersect((r,)))
					yield from ix
					# filter the intersections from r
					ext = [r]
					for nx in ix:
						ext = list(nx.filter(ext))

					# Take the filtered intersections and place
					# them backinto the q so they can be eliminated.
					# Primarily, this is for the edge that doesn't
					# get dropped.
					q.extendleft(ext)

				if not q:
					for y in i:
						q.append(y)
						break
			else:
				# end of i
				# no more intersections possible
				break

	def difference(self, range_set, iter=iter, Queue=collections.deque):
		"""
		# Calculate the difference between two &Set instances.
		# Low-level method. Use (python/operator)`-` for high-level purposes.
		"""

		# self is left side
		i = iter(self)
		q = Queue() # could be a list
		try:
			q.append(next(i))
		except StopIteration:
			# Nothing to emit.
			return

		for x in range_set:
			while q:
				r = q.popleft()

				if r[1] < x[0]:
					# yield r, and get new from q next iteration
					yield r
				elif r[0] > x[1]:
					# put r back into q and get new x by break'ing
					q.appendleft(r)
					break
				else:
					# r, or parts of r, is somewhere inside of x.
					# filter them
					q.extend(x.filter((r,)))

				if not q:
					for y in i:
						q.append(y)
						break
			else:
				# end of i, break as q empty and i has been exhausted
				break
		else:
			# end of subtracting set. emit remainder
			yield from q
			yield from i

	def union(self, range_set):
		"""
		# Calculate the union between two &Set instances.
		"""
		seq = list(range_set)
		seq.extend(self)
		# combine() might not be well suited for this performance-wise.
		return self.__class__.from_normal_sequence(combine(seq))
	__add__ = union

	def __sub__(self, range_set):
		return self.__class__.from_normal_sequence(list(self.difference(range_set)))

	def __or__(self, range_set):
		return self.__class__.from_normal_sequence(list(self.union(range_set)))

class XRange(tuple):
	"""
	# Exclusive numeric range. Only exclusive on the stop.
	# Provides access to zero-sized ranges that need to maintain position.
	"""

	__slots__ = ()

	@property
	def direction(self):
		"""
		# Returns -1 if the stop is less than the start.
		"""
		return 1 if self[0] >= self[1] else -1

	@property
	def start(self):
		"""
		# The beginning of the Range, inclusive.
		"""
		return self[0]

	@property
	def stop(self):
		"""
		# The end of the Range, inclusive.
		"""
		return self[1]

	@classmethod
	def normal(Class, *args):
		"""
		# Create a normal range using the given boundaries; the minimum given will be the
		# start and the maximum will be the stop.
		"""

		return Class((min(*args), max(*args)))

	@classmethod
	def single(Class, index):
		"""
		# Create a range consisting of a single unit.
		"""

		return Class((index, index+1))

	def __contains__(self, x):
		"""
		# Whether or not the range contains the given number.
		"""

		return self[0] <= x < self[1]

	def relation(self, r):
		"""
		# The relation of &r with respect to the &self.
		# Returns `-1` if &r is less than the start; `1` if &r is
		# greater than the stop, and `0` if it is contained.

		# ! WARNING:
			# Does not compensate for negative direction ranges.
		"""

		if r < self[0]:
			return -1
		if r >= self[1]:
			return 1
		# Contained
		return 0

	def contiguous(self, range, tuple=tuple):
		"""
		# Whether the given &range is contiguous with &self.
		"""

		return self[0] in range or self[1]+1 in range

	def join(self, r):
		"""
		# Combine the ranges.
		"""

		return self.normal(min(self[0], r[0]), max(self[1], r[1]))

	def exclusive(self):
		"""
		# Returns &self.
		"""

		return self

	def units(self, step = 1):
		"""
		# Return an iterator to the units in the range.
		"""

		if self.direction > 0:
			return range(self[0], self[1], step)
		else:
			return range(self[0], self[1], -step)

@collections.Mapping.register
class Mapping(object):
	"""
	# A set of ranges associated with arbitrary values.
	"""
	from bisect import bisect

	def __init__(self, combine = operator.methodcaller("__add__")):
		self.set = Set(((),()))
		self.association = {}
		self.combine = combine

	def get(self, key):
		index = self.bisect(self.ranges, (key, key))
