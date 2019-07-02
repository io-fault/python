"""
# Primary public module.

# Provides access to the default Point and Measure types: &Timestamp, &Measure, &Date, &Days.
"""
import operator
import functools

from . import views

__shortname__ = 'libtime'

from .types import *
unix = from_unix_timestamp
from .constants import *
from .sysclock import now

def range(start, stop, step = None, Segment = Segment):
	"""
	# Construct an iterator producing Points between the given &start and &stop.

	# If &step is provided, it will determine the difference to apply to the
	# starting position for each iteration. If it is not provided, the &step
	# defaults to the &.abstract.Point.magnitude of the &start. For dates, the step
	# will be a day, but for timestamps, the magnitude is a nanosecond and will not
	# be ideal for most uses. Usually, a &step should be provided.

	#!/pl/python
		pit = libtime.now()
		week_start = pit.update('day', 1, 'week')
		week_end = begin.elapse(day=7)
		this_week = libtime.range(week_start, week_end, library.Days(1))
	"""
	return Segment((start, stop)).points(step)

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

def zone(name:str=None,
		construct=unix,
		zone_open=functools.lru_cache()(views.Zone.open),
	) -> views.Zone:
	"""
	# Return a Zone object for localizing UTC timestamps and normalizing local timestamps.
	"""

	return zone_open(construct, name)
