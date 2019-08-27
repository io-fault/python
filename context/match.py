"""
# Naive prefix searching implementations.
"""
import collections.abc
import typing

@collections.abc.Mapping.register
class SubsequenceScan:
	"""
	# Subsequence search implementation based on scanning the possible
	# sizes and checking the candidate subsequence's presence in a set.

	# This naive implementation is O(N) (hash checks and subsequence) worst
	# case for first match, so it is inappropriate for large sets.

	# However, when used as part of a tree where the sequence is kept small,
	# it may be a reasonable implmentation selection.

	# [ Properties ]

	# /sequences/
		# The set of sequences that will be scanned by &matches.

	# /sizes/
		# The ordered sequence of slice sizes that sources
		# the match search.

	# /offset/
		# The starting point of the subsequence's slice;
		# usually zero.
	"""

	def __init__(self, sequences:typing.Sequence[typing.Hashable], offset=0, order=True):
		"""
		# Create a SubsequenceScan from the given set of sequences.

		# [ Parameters ]

		# /sequences/
			# A sequence of sequences to scan. Usually, a list of &str instances.
			# This is transformed into a set of sequences.

		# /offset/
			# The start of the subsequence to check; usually `0`.

		# /order/
			# `True` means to match the longest subsequence first, and
			# `False` means to match the shortest first.
			# When `False`, the longest match will never be the first occurrence.
		"""

		self.sequences = set(sequences)
		self.sizes = list(set(map(len, self.sequences))) # get unique sizes
		self.sizes.sort(reverse=order) # largest to smallest
		self.offset = offset
		self.order = order

	def add(self, *values):
		"""
		# Add new values to the set of sequences.

		# ! WARNING:
			# Implementation reconstructs the &sizes sequence every call.
		"""
		self.sequences.update(values)
		self.sizes = list(set(map(len, self.sequences)))
		self.sizes.sort(reverse=self.order) # largest to smallest

	def discard(self, *values):
		"""
		# Remove values from the set of sequences.

		# ! WARNING:
			# Implementation reconstructs the &sizes sequence every call.
		"""
		self.sequences.difference_update(values)
		self.sizes = list(set(map(len, self.sequences)))
		self.sizes.sort(reverse=self.order) # largest to smallest

	def matches(self, key):
		"""
		# Identify all strings in the set that match the given key based
		# on the configured offset.
		"""

		offset = self.offset
		seqset = self.sequences

		for size in self.sizes:
			k = key[offset:offset+size]
			if k in seqset:
				yield k

	def get(self, key, default=None):
		for x in self.matches(key):
			return x
		return default

	def __contains__(self, key):
		for x in self.matches(key):
			return True
		return False

	def __getitem__(self, key):
		"""
		# Get the first match in the set of strings.
		"""
		for x in self.matches(key):
			return x
		raise KeyError(key)

	def values(self):
		return iter(self.sequences)

	def keys(self):
		raise Exception('infinite key set')
