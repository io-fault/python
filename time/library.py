"""
# Primary public module.

# Provides access to the default Point and Measure types: &Timestamp, &Measure, &Date, &Days.
"""
__shortname__ = 'libtime'

from .types import *
unix = from_unix_timestamp
from .constants import *
from .sysclock import now

def field_delta(field, start, stop):
	"""
	# Return the range components for identifying the exact field changes that occurred between two
	# &.abstract.Time instances. This function returns components suitable as input to &range.

	# This function can be used to identify the changes that occurred to a particular field
	# within the given range designated by &start and &stop.

	# [ Parameters ]

	# /field/
		# The name of the unit whose changes will be represented.
	# /start/
		# The beginning of the range.
	# /stop/
		# The end of the range.
	"""
	start = start.truncate(field)
	stop = stop.truncate(field)
	step = start.context.measure_from_unit(field).construct((), {field:1})

	if stop >= start:
		# forwards
		return (start.elapse(step), stop.elapse(step), step)
	else:
		# backwards
		return (start.rollback(step), stop.rollback(step), step)

def business_week(pit, five = Days(5), one = Days(1), list = list):
	"""
	# Return an iterator to the business days in the week of the given &pit.
	"""
	start = Date.of(pit.update('day', 1, 'week'))
	stop = start.elapse(five)
	return list(range(start, stop, one))
