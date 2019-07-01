"""
# Primary public module.

# Provides access to the default Point and Measure types: &Timestamp, &Measure, &Date, &Days.
"""
import operator
import functools
import itertools
import collections
import heapq

from . import views
from . import eternal

__shortname__ = 'libtime'

from .types import *
unix = from_unix_timestamp
from .constants import *
from .sysclock import now

class PartialAttributes(object):
	"""
	# Collect an arbitrary series of identifiers.

	# When called, give the names, arguments, and keywords to the constructor.

	# Chronometry internal use only.
	"""
	__slots__ = ('_construct', '_names')

	def __init__(self, construct, names = ()):
		self._construct = construct
		self._names = names

	def __call__(self, *args, **kw):
		return self._construct(self._names, args, kw)

	@property
	def __dict__(self):
		return {'_construct': self._construct, '_names': self._names}

	def __getattr__(self, name):
		return self.__class__(self._construct, self._names + (name,))

def construct_update(names, args, kw, mc = operator.methodcaller):
	part, of = names
	replacement, = args
	return mc('update', part, replacement, of = of, **kw)

def construct_select(names, args, kw, mc = operator.methodcaller):
	part = names[0]
	if len(names) > 1:
		of = names[1]
	else:
		of = None
	return mc('select', part, of = of, **kw)

def construct_open(names, args, kw, mc = operator.methodcaller):
	container = names[0]
	typ, = args
	def opener(value, *args, **kw):
		return typ.of(**{container: value})
	return opener
# Hide the module from view.
del operator

# Composition constructor for selecting parts from [time] Unit Objects.
# For instance, `select.day.week()`.
select = PartialAttributes(construct_select)

# Composition constructor for updating Time Objects.
# For instance, `update.day.week(0)`.
update = PartialAttributes(construct_update)

# Composition constructor for instantiating [time] Unit Objects from Container types.
#
# from_iso = libtime.open.iso(library.Timestamp)
# pits = map(from_iso, ("2002-01-01T3:45:00",))
#
# Access to standard format parsers are made available:
# &parse_iso8601, &parse_rfc1123.
open = PartialAttributes(construct_open)

# Parse ISO-8601 timestamp strings into a &Timestamp instance.
parse_iso8601 = open.iso(Timestamp)

# Parse RFC-1123 timestamp strings into a &Timestamp instance.
parse_rfc1123 = open.rfc(Timestamp)

# This may end up getting moved, so don't expose it.
del PartialAttributes, construct_update, construct_select, construct_open

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

class Scheduler(object):
	"""
	# All purpose event scheduler.

	# Coorindate the production of events according to a time delay against a monotonic timer.

	# Each instance manages the production of a set of events according to the
	# prescribed delay. When an event is scheduled, the amount of time specified is added to the
	# meter's current position. When the meter surpasses that value, the event is emitted.

	# Events are arbitrary Python objects. Often, they will be tasks to be performed.

	# &Scheduler differs from Python's scheduler as there is no attempt to manage the sleep
	# period. Rather, this responsibility is offloaded onto the user in order to keep
	# functionality isolated.
	"""
	unit = 'nanosecond'

	from .kernel import Chronometer

	def __init__(self,
		Chronometer = Chronometer,
		Identifiers = itertools.count,
		DefaultDict = collections.defaultdict,
		Sequence = collections.deque
	):
		self.meter = Chronometer()
		self.heap = []
		# RPiT to (Eventi) Id's Mapping
		self.schedule = DefaultDict(Sequence)
		self.cancellations = set()

	def period(self):
		"""
		# The period before the next event should occur.

		# When combining Harmony instances, this method can be used to identify
		# when this Harmony instance should be processed.
		"""
		try:
			smallest = self.heap[0]
			return smallest.__class__(smallest - self.meter.snapshot())
		except IndexError:
			return None

	def cancel(self, *events):
		"""
		# Cancel the scheduled events.
		"""
		# Update the set of cancellations immediately.
		# This set is used as a filter by Defer cycles.
		self.cancellations.update(events)

	def put(self, *schedules, push=heapq.heappush) -> int:
		"""
		# Schedules the given events for execution.

		# [ Parameters ]

		# /schedules/
			# The Measure, Event pairs: `(Measure, object), ...`
			# First item of the pairs being an &.abstract.Measure,
			# and the second an arbitrary &object.
		"""
		snapshot = self.meter.snapshot()
		events = []
		try:
			curmin = self.heap[0]
		except:
			curmin = None

		for assignment in schedules:
			measure, event = assignment
			pit = measure.__class__(measure + snapshot)

			push(self.heap, pit)
			self.schedule[pit].append(event)
			events.append(pit)

		return events

	def get(self, pop=heapq.heappop, push=heapq.heappush):
		"""
		# Return all events whose sheduled delay has elapsed according to the
		# configured Chronometer.

		# The pairs within the returned sequence consist of a Measure and the Event. The
		# measure is the amount of time that has elapsed since the scheduled time.
		"""
		events = []
		cur = self.meter.snapshot()
		while self.heap:
			# repeat some work in case of concurrent pop
			item = pop(self.heap)
			overflow = item.__class__(cur - item)

			# the set of callbacks have passed their time.
			if overflow < 0:
				# not ready. put it back...
				push(self.heap, item)
				break
			else:
				# If an identical item has already been popped,
				# an empty set can be returned in order to perform a no-op.
				eventq = self.schedule.pop(item, ())
				while eventq:
					x = eventq.popleft()
					if x in self.cancellations:
						# filter any cancellations
						# schedule is already popped, so remove event and cancel*
						self.cancellations.discard(x)
					else:
						events.append((overflow, x))

		return events
