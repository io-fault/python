"""
This is the primary module for using the datetime types and functions in the
chronometry package.

Unit Knowledge
--------------

All of the following units are defined in the default Time Context. However, the
emphasized units are the only units with designated classes by default.

 Earth
  - second
  - minute
  - hour
  - **day**
  - **week**
  - annum (Julian Year)

 Gregorian
  - **month**
  - year
  - decade
  - century
  - millennium

 Metric Small
  - decisecond
  - centisecond
  - millisecond
  - microsecond
  - **nanosecond**
  - picosecond
  - femtosecond
  - attosecond
  - zeptosecond
  - yoctosecond

 Metric Large
  - decasecond
  - hectosecond
  - kilosecond
  - megasecond
  - gigasecond
  - terasecond
  - petasecond
  - exasecond
  - zettasecond
  - yottasecond

The units in bold are the units with designated Python types. All other units
are expressed in terms of those units unless the time context is explicitly
extended.

Indefinite Units
----------------

Units of unbound quantities of time are called "eternals". They are a special Measure and
Point types that have only three values: zero, infinity, and negative infinity.

The set of possible Measures and Points dealing with eternals are immediately created and
set to the following names:

 Genesis
  The earliest Point in time.

 Never
  The latest Point in time.

 Present
  The current Point in time--always moving.

 Future
  A :py:class:`Segment` whose start is :py:obj:`Present` and end is :py:obj:`Never`.
  ``ts in chronometry.lib.Future``

 Past
  A segment whose start is :py:obj:`Genesis` and end is :py:obj:`Present`.

 Time
  A segment whose start is :py:obj:`Genesis` and end is :py:obj:`Never`.
"""
import sys
import operator
import functools
from . import abstract
from . import libunit # Context & Standard Definitions.
from . import libclock
from . import libzone
from . import eternal

#: Range class.
Segment = libunit.Segment

Context, MeasureTypes, PointTypes = libunit.standard_context(__name__)

#: A tuple containing all of the default Scalar types.
MeasureTypes = MeasureTypes

#: Scalar with finest, default, representation type precision. :py:class:`.abstract.Time`
#: Currently this is nanosecond precision, but chronometry reserves the right to increase the
#: precision across minor versions.
Measure = MeasureTypes[0]

#: Scalar in earth-days. :py:class:`.abstract.Time`
Days = MeasureTypes[1]

#: Scalar in seven earth-days. :py:class:`.abstract.Time`
Weeks = MeasureTypes[2]

#: Scalar in Gregorian Months. :py:class:`.abstract.Time`
Months = MeasureTypes[3]

#: A tuple containing all of the default Point in Time types.
PointTypes = PointTypes

#: Point In Time with Measure's precision. :py:class:`.abstract.Point`
Timestamp = PointTypes[0]

#: Point In Time with earth-day precision. :py:class:`.abstract.Point`
Date = PointTypes[1]

#: Point In Time with seven earth-day precision. :py:class:`.abstract.Point`
Week = PointTypes[2]

#: Point In Time with Gregorian Month precision. :py:class:`.abstract.Point`
GregorianMonth = PointTypes[3]

#: Infinite measure unit.
Eternals = Context.measures['eternal'][None]

#: Infinite unit points. Class used for genesis, never, and now.
Indefinite = Context.points['eternal'][None]

#: Furthest Point in the future.
Never = Indefinite(1)

#: Furthest Point in the past.
Genesis = Indefinite(-1)

#: Current Point in Time, always moving.
Present = Indefinite(0)

#: Segment representing all time. All points in time exist in this segment.
Time = Segment((Genesis, Never))

#: Segment representing the future.
Future = Segment((Present, Never))

#: Segment representing the past.
Past = Segment((Genesis, Present))

#: abstract.Clock interface to the kernel's clock, demotic and monotonic.
kclock = libclock.kclock

#: abstract.Clock interface to the :py:obj:`kclock`
#: that provides Measure and Timestamp instances.
clock = libclock.IClock(kclock, Measure, Timestamp)

#: Shortcut to :py:obj:`.lib.clock.demotic`
now = clock.demotic

# Support for Present to Finite Point
Context.bridge('eternal', 'day', eternal.days_from_current_factory(clock, abstract.Inconceivable))

del sys

def unix(unix_timestamp, Timestamp = Timestamp.of):
	"""
	unix(unix_timestamp)

	Create a :py:class:`.lib.Timestamp` instance
	*from seconds since the unix epoch*.

	Example::

		import chronometry.lib
		x = chronometry.lib.unix(0)
		repr(x)
		# chronometry.lib.Timestamp.of(iso='1970-01-01T00:00:00.000000')
	
	If finer precision is needed for the conversion, elapse the result::

		float = time.time()
		nsecs = int(float)
		us = int((float - nsecs) * 1000000)
		x = chronometry.lib.unix(nsecs)
		x = x.elapse(microsecond=us)
	"""
	return Timestamp(unix=unix_timestamp)

class PartialAttributes(object):
	"""
	Collect an arbitrary series of identifiers.

	When called, give the names, arguments, and keywords to the constructor.
	"""
	__slots__ = ('__construct', '__names')
	def __init__(self, construct, names = ()):
		self.__construct = construct
		self.__names = names

	def __call__(self, *args, **kw):
		return self.__construct(self.__names, args, kw)

	def __getattr__(self, name):
		return self.__class__(self.__construct, self.__names + (name,))

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

#: Composition constructor for selecting parts from [time] Unit Objects.
#: For instance, ``select.day.week()``.
select = PartialAttributes(construct_select)

#: Composition constructor for updating Time Objects.
#: For instance, ``update.day.week(0)``.
update = PartialAttributes(construct_update)

#: Composition constructor for instantiating [time] Unit Objects from Container types.
#: Example::
#:
#:		from chronometry import lib
#:		from_iso = lib.open.iso(lib.Timestamp)
#:		pits = map(from_iso, ("2002-01-01T3:45:00",))
#:
#: Access to standard format parsers are made available:
#: :py:func:`parse_iso8601`, :py:func:`parse_rfc1123`.
open = PartialAttributes(construct_open)

#: Parse ISO-8601 timestamp strings into a :py:class:`Timestamp` instance.
parse_iso8601 = open.iso(Timestamp)

#: Parse RFC-1123 timestamp strings into a :py:class:`Timestamp` instance.
parse_rfc1123 = open.rfc(Timestamp)

# This may end up getting moved, so don't expose it.
del PartialAttributes, construct_update, construct_select, construct_open

def range(start, stop, step = None, Segment = Segment):
	"""
	Construct an iterator producing Points between the given `start` and `stop`.

	If `step` is provided, it will determine the difference to apply to the
	starting position for each iteration. If it is not provided, the `step`
	defaults to the :py:attr:`.abstract.Point.magnitude` of the start.

	Example::

		pit = chronometry.lib.now()
		week_start = pit.update('day', 1, 'week')
		week_end = begin.elapse(day=7)
		this_week = chronometry.lib.range(week_start, week_end, lib.Days(1))
	"""
	return Segment((start, stop)).points(step)

def field_delta(field, start, stop):
	"""
	field_delta(field, start, stop)

	:param field: The name of the unit whose changes will be represented.
	:type field: :py:class:`str`
	:param start: The beginning of the range.
	:type start: :py:class:`.abstract.Time`
	:param stop: The end of the range.
	:type stop: :py:class:`.abstract.Time`

	Return the range components for identifying the exact field changes that occurred between two
	:py:class:`.abstract.Time` instances. This function returns components suitable
	as input to :py:func:`.lib.range`.

	This function can be used to identify the changes that occurred to a particular field
	within the given range designated by `start` and `stop`.
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
	business_week(pit)

	Return an iterator to the business days in the week of the given `pit`.
	"""
	start = Date.of(pit.update('day', 1, 'week'))
	stop = start.elapse(five)
	return list(range(start, stop, one))

def zone(
	name = None,
	construct = unix,
	zone_open = functools.lru_cache()(libzone.Zone.open),
):
	"""
	Return a Zone object for localizing UTC timestamps and normalizing local timestamps.
	"""
	return zone_open(construct, name)
