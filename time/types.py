"""
# Time domain classes for points in time and measures of time.

# Aside from &Segment, all classes in this module are subclasses of &builtins.int.
# Primarily, the time domain classes are constructed using (identifier)`of`:

#!/syntax/python
	y2k = types.Timestamp.of(year=2000)
	two_hours = types.Measure.of(hour=2)

# [ Functions ]

# /&select/
	# Retrieve the most appropriate &core.Measure class available in &Context for use
	# with given the identified unit. Takes one parameter, the unit name.

	#!/syntax/python
		assert issubclass(types.select('hour'), types.Measure)
		assert issubclass(types.select('day'), types.Days)
		assert issubclass(types.select('month'), types.Months)
		assert issubclass(types.select('year'), types.Months)
"""
import typing
from . import core
from ..range import types as rangetypes

Context, MeasureTypes, PointTypes = core.standard_context(__name__)

# A tuple containing all of the default Scalar types.
MeasureTypes = MeasureTypes

# Scalar with finest, default, representation type precision.
# Currently this is nanosecond precision.
Measure = MeasureTypes[0]

# Scalar in earth-days.
Days = MeasureTypes[1]

# Scalar in seven earth-days.
Weeks = MeasureTypes[2]

# Scalar in Gregorian Months.
Months = MeasureTypes[3]

# A tuple containing all of the default Point in Time types.
PointTypes = PointTypes

# Point In Time with Measure's precision.
Timestamp = PointTypes[0]

# Point In Time with earth-day precision.
Date = PointTypes[1]

# Point In Time with seven earth-day precision.
Week = PointTypes[2]

# Point In Time with Gregorian Month precision.
GregorianMonth = PointTypes[3]

# Infinite measure unit.
Eternals = Context.measures['eternal'][None]

# Infinite unit points. Class used for inception, never, and whenever.
Indefinite = Context.points['eternal'][None]

def from_unix_timestamp(unix_timestamp, Timestamp=Timestamp.of):
	"""
	# Create a &Timestamp instance *from seconds since the unix epoch*.

	#!/syntax/python
		assert types.from_unix_timestamp(0) == types.Timestamp.of(iso='1970-01-01T00:00:00.0')

	# For precision beyond seconds, a subsequent elapse can be used.

	#!/syntax/python
		float_ts = time.time()
		nsecs = int(float_ts)
		us = int((float_ts - nsecs) * 1000000)
		x = types.from_unix_timestamp(nsecs)
		x = x.elapse(microsecond=us)
	"""
	return Timestamp(unix=unix_timestamp)

# Select an appropriate &core.Measure class for the given unit name.
select = Context.measure_from_unit

def allocmeasure(unit, quantity=1) -> core.Measure:
	"""
	# Allocate a &core.Measure (subclass) instance for a &quantity of &unit.
	# Where &unit is the name of unit to base the measure on and the &quantity
	# being the number thereof.

	# Uses &select to find the appropriate class.
	"""
	return select(unit).construct((), {unit:quantity})

class Segment(rangetypes.XRange):
	"""
	# A line segment on the time continuum with &Timestamp precision.
	# Two points, inclusive on the start, exclusive on the end.
	"""
	__slots__ = ()
	Type = Timestamp

	@classmethod
	def from_period(Class, start:Timestamp, period:object):
		"""
		# Create a segment from a &start point and the &period between the end.
		"""
		return Class((start, start.elapse(period)))

	def rollback(self, measure:core.Measure):
		"""
		# Create a new segment rolling back both points.
		"""
		return self.__class__((self[0].rollback(measure), self[1].rollback(measure)))

	def elapse(self, measure:core.Measure):
		"""
		# Create a new segment elapsing both points.
		"""
		return self.__class__((self[0].elapse(measure), self[1].elapse(measure)))

	def truncate(self, field:str):
		"""
		# Create a new segment truncating both points to the precision identified by &field.
		"""
		return self.__class__((self[0].truncate(field), self[1].truncate(field)))

	@property
	def endpoint(self) -> Timestamp:
		"""
		# Return the inclusive endpoint of the Segment.
		"""
		return self[1].__class__(self[1]-1)

	def __contains__(self, point):
		return not (
			point.precedes(self.start) \
			or point.proceeds(self.stop)
		)

	def leads(self, pit):
		return self.stop.precedes(pit)
	precedes = leads

	def follows(self, pit):
		return self.start.proceeds(pit)
	proceeds = follows

	def points(self, step:core.Measure) -> typing.Iterable[Timestamp]:
		"""
		# Iterate through all the points within the Segment using the given &step.
		"""
		start = self.start
		stop = self.stop

		if stop >= start:
			# stop >= start
			pos = start
			while pos < stop:
				yield pos
				pos = pos.elapse(step)
		else:
			# stop < start
			pos = start
			while pos > stop:
				yield pos
				pos = pos.rollback(step)
