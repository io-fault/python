=====
Usage
=====

This chapter describes how to use `chronometry`. For detailed reference documentation,
please see the :doc:`reference` chapter.

The primary interface to the functionality provided by chronometry should be accessed
through the :py:mod:`.chronometry.lib` module. It's usage is discussed by this
chapter.

Overview
========

Time classes in chronometry are created by Time Contexts. The default context is
initialized and provided by the :py:mod:`.chronometry.lib` module. The following
lists are the time classes created by that context.

Point In Time types:

 * :py:class:`.chronometry.lib.Timestamp`
 * :py:class:`.chronometry.lib.Date`
 * :py:class:`.chronometry.lib.Week`
 * :py:class:`.chronometry.lib.GregorianMonth`

Measure types:

 * :py:class:`.chronometry.lib.Measure`
 * :py:class:`.chronometry.lib.Days`
 * :py:class:`.chronometry.lib.Weeks`
 * :py:class:`.chronometry.lib.Months`

The interfaces are described by the abstract base classes in
:py:mod:`.chronometry.abstract`. Primarily:

 :py:class:`.chronometry.abstract.Measure`
  A measurement of time.

 :py:class:`.chronometry.abstract.Point`
  A point in time. Points are used to specify calendar dates or
  calendar dates with time of day.

Ranges
------

chronometry includes the class for arbitrary time ranges. They offer more
functionality than the builtin the :py:class:`range` iterator, regarding integers,
but they have similar purposes.

Arbitrary ranges in chronometry are either a pair of :py:class:`.chronometry.abstract.Point`
instances, or a pair of :py:class:`.chronometry.abstract.Measure` instances. Mixing points
and measures in ranges is not necessary as such cases can be easily normalized into
a homogenous pair.

.. _ecc:

Eccentricities
--------------

Points and Measures are Python Integers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This has the effect that integers with the same value will be seen as the same
key in dictionaries::

	>>> from chronometry import lib
	>>> d = {}
	>>> d[lib.Date(0)] = 'Hello, World!'
	>>> print d[0]
	Hello, World!

If type based scoping is needed, the key can be qualified with the type::

   d = {}
   d[(lib.Date, lib.Date(0))] = 'Hello, Date!'
   d[(lib.Timestamp, lib.Timestamp(0))] = 'Hello, Timestamp!'

Or, nested dictionaries could be used::

   d = {lib.Date: {}, lib.Timestamp: {}}
   d[lib.Date][lib.Date(0))] = 'Hello, Date!'
   d[lib.Timestamp][lib.Timestamp(0))] = 'Hello, Timestamp!'

Datetime Math
~~~~~~~~~~~~~

chronometry is heavily based on direct Python `int` subclasses. This offers many
benefits, but it also avoids overriding the integer's operators leaving a,
contextually, low-level operation that should normally be avoided. This likely
offers a suprise as the usual `+` and `-` operators do not perform as they would
with the standard library's `datetime.datetime` or many other datetime packages.

Instead, chronometry relies on the higher-level methods to perform delta
calculation and point positioning.

Day and Month Fields
~~~~~~~~~~~~~~~~~~~~

The `day` and `month` fields of the standard time context are **offsets** and
are not consistent with the usual representation of gregorian day-of-month and
month-of-year. Some of the Container keywords do, however, use the usual
gregorian representation.

More clearly::

	pit = chronometry.lib.Timestamp.of(iso="2002-01-01T00:00:00")
	assert pit.select('day', 'month') == 0
	assert pit.select('month', 'year') == 0

As opposed to the day-of-month and month-of-year fields being equal to `1` as
one might expect them to be. Rather, *they are offsets*.

Month Arithmetic Can Overflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The implementation of month arithmetic is sensitive to the selected day::

	# working with a leap year
	pit = lib.Timestamp.of(iso='2012-01-31T18:55:33.946259')
	pit.elapse(month=1)
	chronometry.lib.Timestamp.of(iso='2012-03-02T18:55:33.946259')

The issue can be avoided by adjusting the PiT to the beginning of the month::

	pit = pit.update('day', 0, 'month')
	pit.elapse(month=1)

Annums and Years
~~~~~~~~~~~~~~~~

The "year" unit in chronometry is strictly referring to gregorian years. This means
that a "year" in chronometry is actually twelve gregorian months, which means *years
are a subjective unit of time*. For *metric* measures--Python timedeltas analog--this
poses a problem in that years should not be used to represent the span when working
with :py:class:`.chronometry.lib.Measure`.

In order to compensate, the :py:class:`.chronometry.lib.Month` class provides a means to
express such subjective time spans.

Unit Aware Comparison
~~~~~~~~~~~~~~~~~~~~~

Unit subclasses do *not* override the built-in comparison methods implemented by the
:py:class:`int` type that all unit classes are based on. Given that these classes can
represent different units, comparisons *must* be performed with *like units* in order
to yield consistently correct results. In order to compensate, unit aware comparisons are
provided for :py:class:`.chronometry.abstract.Point` types:
:py:meth:`.chronometry.abstract.Point.leads` and :py:meth:`.chronometry.abstract.Point.follows`.

Measures do not implement unit-aware comparisons and must be converted to like-units
before the integer comparisons may be used.

Math in :py:mod:`datetime` Terms
--------------------------------

chronometry does not use the usual arithmetic operators for performing datetime
math. Rather, *chronometry uses named methods in order to draw a semantic distinction*.
Not to mention, it is sometimes desirable to use the integer's operators directly
in order to avoid semantics involved with representation types.

The list here points to the abstract base classes.
Points *are* timestamps, datetimes,. Measures *are* intervals, timedeltas.

 ``timedelta() + timedelta()``
  :py:meth:`.chronometry.abstract.Measure.increase`

  ``chronometry.lib.Measure(second=0).increase(chronometry.lib.Measure(second=1))``

 ``timedelta() - timedelta()``
  :py:meth:`.chronometry.abstract.Measure.decrease`

  ``chronometry.lib.Measure(second=2).decrease(chronometry.lib.Measure(second=1))``

 ``datetime() + timedelta()``
  :py:meth:`.chronometry.abstract.Point.elapse`

  ``chronometry.lib.Timestamp().elapse(chronometry.lib.Measure(second=1))``

 ``datetime() - timedelta()``
  :py:meth:`.chronometry.abstract.Point.rollback`

  ``chronometry.lib.Timestamp().rollback(chronometry.lib.Measure(second=1))``

 ``datetime() - datetime()``
  :py:meth:`.chronometry.abstract.Point.measure`

  ``chronometry.lib.Timestamp().measure(chronometry.lib.Timestamp())``

Constructing Points and Measures
================================

A Point is a Point in Time; like a date or a date and time of day. Usually, this
is referring to instances of the :py:class:`.chronometry.lib.Timestamp` class. A Measure
is an arbitrary unit of time and is usually referring to instances the
:py:class:`.chronometry.lib.Measure` class.

.. note:: "Point" may be a misnomer considering that chronometry allows these objects
          to be treated as a vector.

Constructing instances is usually performed with the class method
:py:class:`.chronometry.lib.Measure.of`.
Or, :py:class:`.chronometry.lib.Timestamp.of` for Points.

Creating a Timestamp
--------------------

The :py:class:`.chronometry.lib.Timestamp` type is the Point In Time Representation
Type with the finest precision available *by default*::

	near_y2k = chronometry.lib.Timestamp.of(date=(2000,1,1), hour=8, minute=24, second=15)
	>>> near_y2k
	chronometry.lib.Timestamp.of(iso='2000-01-01T08:24:15.000000')

Currently, The :py:class:`.chronometry.lib.Timestamp` and :py:class:`.chronometry.lib.Measure` types
use nanosecond precision.

.. warning:: The project *may* increase the precision of Timestamp and Measure in
             the future so it is important to avoid presumptuous code when possible.

Creating a Date
---------------

A Date is also considered a Point In Time type. The Date type exists for the
purpose of representing the point in which the specified day starts, *and* the
period between that point and the start of the next day; non-inclusive::

	chronometry.lib.Date.of(year=1982, month=4, day=17) # month and day are offsets.
	chronometry.lib.Date.of(iso='1982-05-18')

While a little suprising, the above reveals an apparent inconsistency: the
`month` keyword parameter acts as a month offset. To compensate,
the `date` container keyword parameter is treated specially to accept
gregorian calendar representation. The keyword parameters are literal
increments of units. Subsequently, using the `date` container can more
appropriate::

	>>> chronometry.lib.Date.of(date=(1982,5,18))
	chronometry.lib.Date.of(iso='1982-05-18')

Getting the Current Point in Time
---------------------------------

The primary interface for accessing the system clock is using the
:py:func:`.chronometry.lib.now` callable::

	current_time = chronometry.lib.now()

The returned timestamp is a UTC timestamp.

.. note:: Using the system time for managing timeouts is discouraged.
          chronometry's clock interface has monotonic devices for managing timeouts.

Creating a Timestamp from an ISO-9660 String
--------------------------------------------

While the :py:mod:`.chronometry.libformat` module manages the details, the
:py:mod:`.chronometry.lib` module provides access to the functionality::

	ts = chronometry.lib.Timestamp.of(iso='2009-02-01T3:33:45.123321')

chronometry provides parsers for both ISO-9660 and RFC-1123 datetime formats. The
above example shows how to construct a Point in Time from an ISO-9660 string.
The following shows RFC-1123, the format used by HTTP::

	ts = chronometry.lib.Timestamp.of(rfc='Sun, 19 Mar 2012 07:27:58')

For direct callable access to this functionality, the `Openers`_ functionality
should be used::

	parse_iso_to_ts = chronometry.lib.open.iso(chronometry.lib.Timestamp)
	ts = parse_iso_to_ts('2009-02-01T3:33:45.123321')

Formatting a Standard Timestamp
-------------------------------

Likewise, instances can be formatted by the standards::

	ts = chronometry.lib.Timestamp.of(iso='2009-01-01T7:30:0')
	print(ts.select('iso'))

And RFC as well::

	assert "Sat, 01 Jan 2000 00:00:00" == chronometry.lib.Timestamp(date=(2000,1,1)).select('rfc')

Constructing a Timestamp from Parts
-----------------------------------

A :py:class:`.chronometry.lib.Timestamp` can be constructed from time parts using the
:py:meth:`.chronometry.abstract.Time.of` class method. This method takes
arbitrary positional parameters and keyword parameters whose keys are the name
of a unit of time known by the time context::

	ts = chronometry.lib.Timestamp.of(hour = 55, second = 78)

Notably, the above is not particularly useful without a date::

	chronometry.lib.Timestamp.of(
		date = (2015, 1, 1),
		hour = 13, minute = 7,
		second = 4,
		microsecond = 324159
	)

Constructing a Timestamp from a UNIX Timestamp
-----------------------------------------------

The `unix` container keyword provides an interface from seconds since the
UNIX-epoch, "January 1, 1970". A timestamp can be made using the
:py:meth:`.chronometry.abstract.Time.of` method::

	epoch = chronometry.lib.Timestamp.of(unix=0)

Subseqently, a given PiT can yield a UNIX timestamp using the
:py:meth:`.chronometry.abstract.Time.select` method::

	now = chronometry.lib.now()
	unix = now.select('unix')

Alternatively, the :py:obj:`.chronometry.lib.open` composition constructor can be used
to build a callable that returns :py:class:`.chronometry.lib.Timestamp` instances::

	from_unix = chronometry.lib.open.unix(chronometry.lib.Timestamp)

And a contrived use-case where the file `f` contains lines containing unix timestamps::

	with open(...) as f:
		times = list(map(from_unix, map(int, f.readlines())))

Arithmetic of Points and Measures
=================================

chronometry's time types are all based on subclasses of Python's :py:class:`int`.
The usual arithmetic operators are essentially low-level operations that can be
used in certain cases, but they should be restricted to performance critical
situations where the higher-level methods cannot be used.

Getting a Particular Day of the Week
------------------------------------

Points and scalars can both update arbitrary fields according to a boundary.
With Timestamps and Dates aligned on the beginning of a week, an arbitrary
day of week can be found by field modification::

	ts = chronometry.lib.Timestamp.of(iso="2000-01-01T3:30:00")
	>>> print(ts.select('day', 'week'))
	6
	ts = ts.update('day', 1, 'week') # 0-6, Sun-Sat.
	>>> print(ts)
	'1999-12-27T03:30:00.000000'
	>>> print(ts.select('weekday'))
	'monday'

By extension, to get the following Monday, just add seven!::

	ts = chronometry.lib.Timestamp.of(iso="2000-01-01T3:30:00")
	ts = ts.update('day', 8, 'week')
	>>> print(ts)
	'2000-01-03T03:30:00.000000'
	>>> print(ts.select('weekday'))
	'monday'

Or, to get the preceding Monday, just substract seven::

	ts = chronometry.lib.Timestamp.of(iso="2000-01-01T3:30:00")
	ts = ts.update('day', 1-7, 'week')
	print(ts)
	# '1999-12-20T03:30:00.000000'
	print(ts.select('weekday'))
	# 'monday'

And so on: 1+|-14, 1+|-21...

Getting a Particular Weekday of a Month
---------------------------------------

Occasionally, the need may arise to fetch the N-th weekday of the month. This is
trickier than getting an arbitrary weekday as it requires the part to be aligned
on a month. Given an arbitrary time type supporting gregorian units, `ts`, the
month must first be adjusted to the beginning of the month::

	# Find the third Saturday of the month.
	ts = chronometry.lib.Timestamp.of(...)

	# Get the first of the month.
	ts = ts.update('day', 0, 'month')
	# Now the first Saturday of the month.
	ts = ts.update('day', 6, 'week')
	ts.elapse(day=14)

The above, however, is hiding a factor due to Saturday's nature of being on
the end of the week: alignment. Alignment allows the repositioning of the
boundary that a part is selected from or updated by. This provides the ability
to designate that a particular weekday be the beginning or end of the week.
Subsequently, allowing quick identification::

	ts = chronometry.lib.Timestamp.of(...)
	# Get the last day of the Month.
	ts = ts.elapse(month=1).update('day', -1, 'month')
	ts.update('day', 0, 'week', align=-2)

Eternal Measures and Points
===========================

`chronometry` defines eternal units of time that are of Indefinite non-zero periods. These units are used to
define the very beginning, the current, and the very end of time: :py:obj:`.lib.Genesis`,
:py:obj:`.lib.Present`, :py:obj:`.lib.Never`. These points in time are ambiguous and have simple rules
when used with finite points in time. Never is a point in the future that is greater than
all other points, Genesis is a point in the past before all other points, and Present
is a continually moving point representing the current point in time, which is a subjective concept normally
defined by the system's wall clock time.
Like other Points in Time, there are corresponding measures: positive and negative eternity, but are
not commonly referred to or used.

Eternals also allow for the creation of indefinite segments. There are three built-in
segments: :py:obj:`.lib.Time`, :py:obj:`.lib.Past`, :py:obj:`.lib.Future`. These segments
represent common concepts that can be used to identify whether or not a given point has
already occurred or will occur as Present, the start or stop of the segments, is a
continually moving point in time.

Indefinite points such as Never and Genesis are also useful for creating unbounded
segments from a particular point in time::

   pit = chronometry.lib.now().rollback(hour=1)
   rfuture = chronometry.lib.Segment((pit, chronometry.lib.Never))

The `rfuture` segment starts an hour in the past and never ends. Notably, iterators
created by the segment are continuous in the future::

   hourly = rfuture.points(chronometry.lib.Measure.of(hour=1))
   for x, ts in zip(range(3), hourly):
      print(x, ts)

Managing sets of unbounded segments are the recommended way to manage recurring jobs.

Working with Sets and Sequences
===============================

The accessor and manipulation methods provide a high level interface to an
individual PiT or scalar, but often an operation needs to be applied
*efficiently* to a set or sequence of Time Objects.

The :py:mod:`.chronometry.lib` module has a few tools for
constructing--FP'ish--compositions for extraction, manipulation, and creation.

 * :py:obj:`.chronometry.lib.select`
 * :py:obj:`.chronometry.lib.update`
 * :py:obj:`.chronometry.lib.open`

Using these objects to construct selectors and manipulations is often desirable
over `generator expressions` as it allows a reference to the desired transformation.

.. note::
   Currently these compositions work directly with the presented interfaces,
   so the implementation only offers syntactic convenience. Future versions will
   provide implementations that offer greater efficiency.

Selectors
---------

The :py:obj:`.chronometry.lib.select` constructor provides a syntactically convenient
means to select fields from an arbitrary Time Object.

For instance, ``map(chronometry.lib.select.timeofday(), iter(obj))``, will perform an
operation consistent to: ``(x.select('timeofday') for x in iter(obj))``.

In the case where the `whole` needs to be specified, a second attribute may be
given::

	hour_of_day = chronometry.lib.select.hour.day()
	>>> print(hour_of_day(chronometry.lib.Timestamp.of(datetime=(2001,1,1,4,30,2))))

Updaters
--------

The :py:obj:`.chronometry.lib.update` constructor provides a syntactically convenient
means to update *a* field of an arbitrary Time Object.

For instance, ``map(chronometry.lib.update.day.week(0), iter(obj))``, will perform an
operation consistent to: ``(x.update('day', 0, 'week') for x in iter(obj))``

Field updates can provide a concise means to simplify some rather tricky
date-time math.

Openers
-------

There is often a need to construct an opener. Instantiating timestamps from
date-time tuples, ISO formatted timestamps, and UNIX timestamps is common.

The :py:obj:`.chronometry.lib.open` constructor provides a syntactically convenient
means of doing so.

Open is different from Select and Update as it is primarily concerned with
instantiation. Therefore, the desired type to "open into" must be specified as a
parameter to the constructor.

Common forms:

 ``chronometry.lib.open.unix(chronometry.lib.Timestamp)``
  Given an integer relative to the UNIX epoch, return a
  corresponding :py:class:`.chronometry.lib.Timestamp` instance.

 ``chronometry.lib.open.iso(chronometry.lib.Timestamp)``
  Given an ISO formatted string, return a
  corresponding :py:class:`.chronometry.lib.Timestamp` instance.

 ``chronometry.lib.open.iso(chronometry.lib.Date)``
  Same as the varient taking the timestamp, but align the Point to the date.

 ``chronometry.lib.open.rfc(chronometry.lib.Timestamp)``
  Like the ISO variant, but take an RFC complient string.
  This is notably useful when working with HTTP.

 ``chronometry.lib.open.datetime(chronometry.lib.Timestamp)``
  Build a constructor that takes seconds from the UNIX epoch and returns a
  :py:class:`.chronometry.lib.Timestamp` instance.


Working with the Clock
======================

chronometry has the concept of a clock. This clock has multiple services for tracking
the passing of time according to the "clockwork" of the underlying operating
system. This includes monotonic passing of time, and "demotic", colloquial.

The :py:mod:`.chronometry.libclock` module provides the implementation of the
:py:class:`.chronometry.abstract.Clock` interface using the :py:mod:`.chronometry.system`
module. The :py:mod:`.chronometry.system` module uses whatever facilities it was able
to find at compile time in order to provide maximum precision.

Demotic and Monotonic Time
--------------------------

Clocks have two concepts of time, the demotic and monotonic. The rate of change
of demotic time is mutable and the monotonic time is, ideally, immutable.

.. note:: The designation of "demotic time" is not common.

Demotic time is the UTC standard wall clock time and is often referred to
ambiguously as it is generally assumed to be the desired perspective of time.
chronometry even refers to this ambiguously as "now", :py:func:`.chronometry.lib.now`.

Monotonic time is the amount of time that has elapsed from some arbitrary point
and chronometry denotes that by only returning :py:class:`.chronometry.lib.Measure`
instances for representing monotonic time.

Direct use of the :py:meth:`.chronometry.clock.monotonic` method is not
recommended for most cases. Rather, chronometry provides some iterators and
context managers that cover the common use-cases of monotonic time.

Time Meters
-----------

Time meters, :py:meth:`.chronometry.lib.clock.meter`, are iterators provided by
:py:class:`.chronometry.abstract.Clock` implementations that track the amount of time
that has elapsed since the *first* iteration::

	for x in chronometry.lib.clock.meter():
		print(repr(x))
		if x.select('second') > 1:
			break

Meters are perfect for polling situations with timeouts.

Delta Meters
------------

In other cases, the total time is not particularly interesting or needs be
calculated by another component of the process. Delta meters,
:py:meth:`.chronometry.lib.clock.delta` are iterators that yield the amount of time
that has elapsed since the *prior* iteration.

Delta meters are good for implementing rate limiting::

	total = chronometry.lib.Measure()
	for x in chronometry.lib.clock.delta():
		print(repr(x))
		total = total.elapse(x)
		if x.__class__(total).select('second') > 1:
			break


Tracking Arbitrary Units over Time
==================================

Using the same underlying functionality as :py:meth:`.chronometry.lib.clock.delta`,
the :py:mod:`.chronometry.libflow` module provides tools for tracking units over time
for a set of objects.

Instances of the :py:class:`.chronometry.libflow.Radar` class manage the tracked
units over a period of time for a given set of objects. It keeps records of the
given units associated with the amount of time that has elapsed since the last
record was made. The time deltas are ultimately collected using the system's
monotonic clock.

By default, Radars use weak references in order to identify when there is no
need to keep records on an object. In order to begin tracking an object's
units, just start tracking::

	import socket
	from chronometry import libflow
	s = socket.socket()
	R = libflow.Radar()
	units = 0
	R.track(s, units)

This creates a record associated with the socket object `s` noting zero units.
However, usually it is best to wait until an actual transfer occurs before tracking
an object. When an object is tracked for the first time, its corresponding
chronometer is started.
Subsequently, the initial rate information may be skewed by additional time.

Everytime the units of an object are tracked, :py:meth:`.chronometry.lib.Radar.track`,
a new record is created.

.. warning:: The number of records can grow unbounded unless some maintenance is performed.

There are two methods for maintenance:
:py:meth:`.chronometry.lib.Radar.collapse` and :py:meth:`.chronometry.lib.Radar.truncate`.

In cases where the overall rate is desired, collapse provides the necessary
functionality to aggregate the records::

	R = libflow.Radar()
	data = processdata()
	R.track(ob, len(data))
	data = processdata()
	R.track(ob, len(data))
	R.collapse(ob) # "ob" now has one record associated with it

In cases where the interest only lies in a previous window, truncate will trim
the records according to the window's specification::

	R = libflow.Radar()
	data = processdata()
	R.track(ob, len(data))
	data = processdata()
	R.track(ob, len(data))
	records_before_last_six_seconds = R.truncate(ob, lib.Measure.of(second=6))
	rate_over_last_six_seconds = R.rate(ob)

In cases where both are desired, the collapse method can be given a window. The
total resource consumption is entirely recorded while the specified window's
consistency is maintained.


Working with Time Zones
=======================

**Time zones are difficult**. In the best situations, use is not necessary, but that is,
unfortunately, not often. Time zones offer a rather unique problem as programmers are
indirectly forced into supporting designations often defined by local government. This
imposition complicates the situation dramatically. Even in the case where the right
process is followed, it is possible to come to the wrong conclusion given rotten time zone
information.

There is no easy mode when being time zone aware. It's an extra level of detail that
*must* be managed by the application.

Understanding Time Zones
------------------------

The difficulty of time zones stems from the need to transition to and from an
offset for appropriating the representation of a Point in Time. This is referring to
a couple tasks:

 * Representing a UTC Point in Time in a local form.
 * Converting a local form to a UTC Point in Time.

While this is trivial on the face, the local form is actually a moving target. A
time zone database is maintained by a standards body in order to keep
track of how the local form varies. Often this involves daylight savings time,
but extends into situations where political decisions alter the offsets for a
given region altogether. At a wider scope the database *can* change entirely.
Consider database corrections, updates, or complete substitutions.

This subjective offsetting can create situations where a given time of day
of a local form *is either ambiguous or invalid*. Proper handling of these cases
is often dependent on the context in which a given local form is being used.

When working with zoned PiTs, there are two situations:

 1. A canonical PiT, normally a PiT in UTC associated with a zone.
 2. A local PiT where the local form is being represented

Each situation has its own requirements for proper zone handling.

In the first, the zone identifier should be associated with the PiT object.
These objects should always be a type capable of designating a date and time of
day, the :py:class:`.chronometry.lib.Timestamp` type. Representation types like
:py:class:`.chronometry.lib.Date` don't require zone adjustments unless it
is ultimately intended to refer to the beginning of the day in that particular
zone in UTC.

In the second, the actual offset *and* zone identifier applied to the zone
should be associated with the PiT object.

Getting an Offset from a UTC Point in Time
------------------------------------------

While :py:mod:`.chronometry.libzone` provides the implementation of Zone objects, high level
access is provided via the :py:func:`.chronometry.lib.zone` function::

   tz = chronometry.lib.zone('America/Los_Angeles')
   pit = chronometry.lib.now()
   offset = tz.find(pit)

Once the :py:class:`.chronometry.libzone.Offset` object has been found for a given point in
time, the UTC point can be adjusted::

   la_pit = pit.elapse(offset)

Localizing a UTC Point in Time
------------------------------

The examples in the previous section show the details of localization.
:py:class:`.chronometry.libzone.Zone` instances have the above functionality packed into a
single method, :py:meth:`.chronometry.libzone.Zone.localize`::

   pit, offset = chronometry.lib.zone().localize(chronometry.lib.now())

The offset applied to the point in time is returned with the adjusted point as it is
often necessary in order to properly represent the timestamp::

   offset.iso(pit)
   "2013-01-17T15:36:35.834813000 PST-28800"

Normalizing a Local Point in Time
---------------------------------

Normalization is the process of adjusting a localized timestamp by its *known* offset into
a UTC timestamp and then localizing it. The :py:meth:`.chronometry.libzone.Zone.normalize`
method has this functionality::

   pit, offset = chronometry.lib.zone().localize(chronometry.lib.now())
   normalized_pit, new_offset = chronometry.lib.zone().normalize(offset, pit)

Where `normalized_pit` and `new_offset` are the *exact* same objects if no change was
necessary.
