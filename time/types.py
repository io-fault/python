"""
# Time domain classes for points in time and measures of time.

#!python
	y2k = types.Timestamp.of(year=2000)
	two_hours = types.Measure.of(hour=2)

	# # Timestamp addition.
	ts = y2k.elapse(two_hours, minute=2)

	# # Type aware comparisons.
	assert y2k.leads(ts) == True
	assert y2k.follows(ts) == False

# [ Elements ]

# /select/
	# Retrieve the most appropriate &abstract.Measure class available in &Context for use
	# with the identified unit.

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
	# Necessary for representing months in certain cases as &Measure
	# is in exact nanoseconds.
"""
from typing import Union
from . import abstract
from . import core

Context, MeasureTypes, PointTypes = core.standard_context(__name__)

# A tuple containing all of the default Scalar types.
MeasureTypes = MeasureTypes

# Point In Time with Measure's precision.
Timestamp = PointTypes[0]

# Point In Time with earth-day precision.
Date = PointTypes[1]

# Scalar with finest, default, representation type precision.
# Currently this is nanosecond precision.
Measure = MeasureTypes[0]

# Scalar in Gregorian Months.
Months = MeasureTypes[2]

# A tuple containing all of the default Point in Time types.
PointTypes = PointTypes

def from_unix_timestamp(unix_ts:Union[int,float], *, Timestamp=Timestamp.of) -> Timestamp:
	"""
	# Create a &Timestamp instance *from seconds since the unix epoch*.

	#!python
		assert types.from_unix_timestamp(0) == types.Timestamp.of(iso='1970-01-01T00:00:00.0')

	# For precision beyond seconds, a float and be given or a subsequent
	# &abstract.Point.elapse may issued.
	"""
	return Timestamp(unix=unix_ts)

select = Context.measure_from_unit
