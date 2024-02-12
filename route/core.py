"""
# Implementation of the route base class and route tools.

# The primary class, &PartitionedSequence, is essentially a unrolled linked list
# leveraging Python's reference counting to allow sharing of routes and segments
# across instances.

# Direct use of this class is likely inappropriate. Either &.types.Selector or &.types.Segment
# should be subclassed in order to convey the presence of a target resource.
"""
from collections.abc import Iterable, Iterator, Sequence, Hashable
from typing import TypeVar, Generic, Optional
import functools

from ..context.tools import cachedcalls, consistency

# The points along a path.
Identifier = TypeVar('Identifier', bound=Hashable)

# Reduction for often re-used PartitionedSequence.points
def vcombine(*args):
	return args
partition_cache = cachedcalls(32)(vcombine)

def join(head:Sequence[Identifier], tail:Sequence[Identifier]) -> Sequence[Identifier]:
	return partition_cache(*head, *tail)
absolute_cache = cachedcalls(64)(join)

@cachedcalls(32)
def construct_cache(Class, context, points):
	return Class(context, points)

def map_partitions(parts):
	# Utility for mapping absolute indexes to partitioned indexes
	i = 0
	for p in parts:
		yield from ((i, x) for x in range(len(p)))
		i += 1

def relative_path(target, source) -> tuple[int, int, Sequence[Identifier]]:
	# Produce information for forming a relative path.
	# PartitionedSequence specific details; used by correlate and segment.
	if source.context is target.context:
		from_path = source.points
		target_path = target.points
	else:
		from_path = source.absolute
		target_path = target.absolute

	cl = consistency(from_path, target_path)

	return cl, len(from_path), target_path

@functools.total_ordering
class PartitionedSequence(Generic[Identifier]):
	"""
	# Route implementation class managing the path as a partitioned sequence.

	# The stored sequences are usually tuples that are connected to a Context
	# instance defining the preceeding points in the path. The intent of the
	# structure is to allow path sharing for reducing memory use when working
	# with long paths. However, this is not done automatically and the exact
	# usage must be aware of how &context can eliminate redundant leading segments.
	"""
	context: Optional['PartitionedSequence']
	points: Sequence[Identifier]

	def correlate(self, target) -> tuple[int, Sequence[Identifier]]:
		"""
		# The relative positioning of &self with respect to &target.
		# Provides the necessary information to form a relative path to &target from &self.

		# Returns the number of steps to ascend and the sequence of identifiers to apply in
		# order to arrive at &target.
		"""
		path: Sequence[Identifier]
		cl, l, path = relative_path(target, self)
		asecent = l - cl
		segment = path[cl:]

		return (asecent, segment)

	@classmethod
	def from_sequence(Class, points, context=None, chunksize=4):
		r = None

		for i in range(0, len(points), chunksize):
			r = Class(context, partition_cache(*points[i:i+chunksize]))
			context = r

		return r if r is not None else Class(None, ())

	# Partition Interfaces

	@classmethod
	def from_partitions(Class, parts:Iterable[Sequence[Identifier]], context=None):
		"""
		# Construct a new instance from an iterable of partitions in root order.
		"""
		for points in parts:
			context = construct_cache(Class, context, partition_cache(*points))

		return context if context is not None else construct_cache(Class, None, ())

	def from_context(self, *paths:Identifier):
		"""
		# Construct a new route relative to &self.context.
		"""
		return self.__class__(self.context, paths)

	def delimit(self):
		"""
		# Create a new partitioned sequence designating &self as the context.

		# If the context-relative path of &self is an empty sequence, &self is returned exactly.
		"""
		if self.points:
			return self.__class__(self, ())
		else:
			return self

	def iterpartitions(self):
		"""
		# Produce the *partitions* of the sequence in inverse order.

		# The identifiers *inside* the partitions will be in root order.
		"""
		x = self
		while x.context is not None:
			yield x.points
			x = x.context
		yield x.points

	def partitions(self, list=list):
		"""
		# Construct a sequence of partitions in root order.
		# Result is a suitable parameter for &from_partitions.
		"""
		l = list(self.iterpartitions())
		l.reverse()
		return l

	def __init__(self, context, points:Sequence[Identifier]):
		self.context = context
		self.points = points

	def __repr__(self):
		return "%s.from_partitions(%r)" %(self.__class__.__name__, self.partitions())

	def __reduce__(self):
		return (self.from_partitions, (self.partitions(),))

	def __hash__(self) -> int:
		return hash(self.absolute)

	def __eq__(self, operand, isinstance=isinstance):
		if isinstance(operand, self.__class__):
			if self.context is operand.context:
				return self.points == operand.points

			# Compare absolute
			return self.absolute == operand.absolute

	def __lt__(self, operand, isinstance=isinstance):
		if isinstance(operand, self.__class__):
			if self.context is operand.context:
				return self.points < operand.points

			return self.absolute < operand.absolute

	# Sequence Interfaces

	def __len__(self):
		return sum(map(len, self.iterpartitions()))

	def __iter__(self) -> Iterator[Identifier]:
		for p in self.partitions():
			yield from p

	def __contains__(self, operand):
		for p in self.iterpartitions():
			if operand in p:
				return True

		return False

	def __getitem__(self, req):
		return self.absolute[req]

	def __add__(self, tail:Iterable[Identifier], list=list):
		t = list(tail)
		if t:
			return self.__class__(self.context, partition_cache(*self.points, *t))
		else:
			return self

	# Route Interfaces

	def __truediv__(self, addition:Identifier):
		return self.__class__(self.context, self.points + (addition,))

	def __floordiv__(self, route):
		if isinstance(route, PartitionedSequence):
			return self.from_partitions(route.partitions(), context=self)

		return NotImplemented

	def __mul__(self, replacement:Identifier):
		if not self.points:
			return self.container / replacement

		return self.__class__(self.context, partition_cache(*self.points[:-1], replacement))

	def __pow__(self, strip:int, range=range):
		if strip < 0:
			strip = len(self) + strip

		y = self
		# This is not efficient, but it preserves the partitions.
		for x in range(strip):
			y = y.container
		return y

	def __rshift__(self, segment):
		current = self
		for p in segment.partitions():
			for x in p:
				current /= x
				yield current

			current = current.delimit()

	def __lshift__(self, segment):
		state = self // segment

		for i in range(len(segment)):
			yield state
			state = state.container

	def __invert__(self):
		x = self
		for i in range(len(x)):
			yield x
			x = x.container

	def __xor__(self, operand):
		ascent, segment = self.correlate(operand)

		x = self
		for i in range(ascent):
			yield x
			x = x.container

		yield x

		path = []
		for y in segment:
			path.append(y)
			yield x + path

	def iterpoints(self):
		x = self
		seq = []
		add = seq.append
		while x.context is not None:
			add(x.points)
			x = x.context
		add(x.points)

		for i in reversed(seq):
			yield from i

	def iterinverse(self):
		x = self
		while x.context is not None:
			yield from reversed(x.points)
			x = x.context

		yield from reversed(x.points)

	@property
	def absolute(self) -> Sequence[Identifier]:
		r:Sequence[Identifier] = self.points
		x = self
		while x.context is not None:
			r = absolute_cache(x.context.points, r)
			x = x.context
		return r

	@property
	def identifier(self):
		if self.points:
			return self.points[-1]
		else:
			if self.context is not None:
				return self.context.identifier
			return None

	@property
	def root(self):
		return self.__class__(self.context, partition_cache(*self.points[0:1]))

	@property
	def container(self):
		ctx = self.context
		p = self.points

		while not p and ctx is not None:
			p = ctx.points
			ctx = ctx.context

		return self.__class__(ctx, partition_cache(*p[:-1]))
