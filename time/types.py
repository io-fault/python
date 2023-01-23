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

select = Context.measure_from_unit

if True:
	def _s_format_date(cd:Date) -> str:
		y, m, d = cd.select('date')
		return f"{y}-{m:02}-{d:02}"
	def _r_format_date(cd:Date) -> str:
		y, m, d = cd.select('date')
		return f"(time.date@'{y}-{m:02}-{d:02}')"
	Date.__repr__ = _r_format_date
	Date.__str__ = _s_format_date

	def _r_format_timestamp(ts:Timestamp) -> str:
		s = ts.select('iso')
		return f"(time.stamp@'{s}')"
	Timestamp.__repr__ = _r_format_timestamp

	def _r_format_measure(q:Measure) -> str:
		ufields = [
			'd', 'h', 'm', 's',
			'ms', 'us', 'ns',
		]

		uv = zip(ufields, [
			q.select('day'),
			q.select('hour', 'day'),
			q.select('minute', 'hour'),
			q.select('second', 'minute'),
			q.select('millisecond', 'second'),
			q.select('microsecond', 'millisecond'),
			q.select('nanosecond', 'microsecond'),
		])

		units = '.'.join([str(v)+u for u, v in uv if v != 0])
		return f"(time.measure@'{units}')"
	Measure.__repr__ = _r_format_measure
