"""
# Segment and Selector implementation access.
"""
import itertools
from . import core
from . import rewrite

consistency = core.consistency # Ultimately from fault.context.tools

class Segment(core.PartitionedSequence[core.Identifier]):
	"""
	# Sequence of identifiers that may be incorporated into a selector subclass.
	"""

	__slots__ = ('context', 'points',)

	def __str__(self):
		parts = ["->".join(x) for x in self.iterpartitions()]
		return ''.join("(" + x + ")" for x in parts)

	def __bool__(self):
		"""
		# True is the segment has any points; False if zero.
		"""
		for x in self.iterpartitions():
			if x:
				return True

		return False

	def segment(self, from_stem=None,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		):
		if self.context is from_stem:
			return Cache(self.__class__, None, self.points)
		elif from_stem is None:
			return self

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(self.__class__, None, ())

		return self.__class__(None, seg[cl:])

class Selector(core.PartitionedSequence[core.Identifier]):
	"""
	# Route domain base class.

	# Subclasses provide access methods to a resource identified
	# by the sequence of identifiers contained within the selector instance.
	"""

	def segment(self, from_stem=None,
			Segment=Segment,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		) -> Segment:
		"""
		# Construct a &Segment from &self starting at the position designated by &from_stem.
		# If stem is not given, the entire selector will be converted.
		"""
		if self.context is from_stem:
			return Cache(Segment, None, self.points)
		elif from_stem is None:
			return Segment.from_partitions(self.partitions())

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(Segment, None, ())

		return Segment(None, seg[cl:])

	def __str__(self):
		parts = ["/".join(x) for x in self.iterpartitions()]
		return ''.join("[" + x + "]" for x in parts)

	def __bool__(self):
		# Subclasses with another opinion on selector truth should override.
		return True

	_relative_resolution = staticmethod(rewrite.relative)
