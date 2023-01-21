"""
# Time domain classes for points in time and measures of time.

#!python
	y2k = types.Timestamp.of(year=2000)
	two_hours = types.Measure.of(hour=2)

# [ Elements ]

# /select/
	# Retrieve the most appropriate &core.Measure class available in &Context for use
	# with given the identified unit. Takes one parameter, the unit name.

	#!python
		assert issubclass(types.select('hour'), types.Measure)
		assert issubclass(types.select('month'), types.Months)
		assert issubclass(types.select('year'), types.Months)

# /Timestamp/
	# The nanosecond precision point in time type.
# /Date/
	# The earth-day precision point in time type.
# /Measure/
	# The nanosecond precision time delta type.
# /Months/
	# The gregorian month precision time delta type.
"""
from collections.abc import Iterable
from . import abstract
from . import core
from ..range import types as rangetypes

Context, MeasureTypes, PointTypes = core.standard_context(__name__)

# A tuple containing all of the default Scalar types.
MeasureTypes = MeasureTypes

# Scalar with finest, default, representation type precision.
# Currently this is nanosecond precision.
Measure = MeasureTypes[0]

# Scalar in Gregorian Months.
Months = MeasureTypes[2]

# A tuple containing all of the default Point in Time types.
PointTypes = PointTypes

# Point In Time with Measure's precision.
Timestamp = PointTypes[0]

# Point In Time with earth-day precision.
Date = PointTypes[1]

# Infinite measure unit.
Eternals = Context.measures['eternal'][None]

# Infinite unit points. Class used for inception, never, and whenever.
Indefinite = Context.points['eternal'][None]

def from_unix_timestamp(unix_timestamp, Timestamp=Timestamp.of):
	"""
	# Create a &Timestamp instance *from seconds since the unix epoch*.

	#!python
		assert types.from_unix_timestamp(0) == types.Timestamp.of(iso='1970-01-01T00:00:00.0')

	# For precision beyond seconds, a subsequent elapse can be used.

	#!python
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
