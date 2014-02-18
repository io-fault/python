"""
Time is an illusion?

⌛ About
--------

.. warning:: rhythm is a work in progress.

rhythm is a pure-Python datetime package based on the built-in Python `int`.
By default, timestamps have nanosecond precision granting common applications
more than enough detail about a point in time. For specialized purposes, the
units handled by rhythm can be arbitrarily extended--the `int` subclasses
represent a designated unit and a common Time Context, group of unit classes,
provides the necessary linkage and transformations for conversion across
classes.

Calendar Support:

 * Proleptic Gregorian

rhythm's APIs are *not* compatible with the standard library's datetime module. *On purpose.*

The surface functionality is provided in :py:mod:`.rhythm.lib`::

	import rhythm.lib

Current date and time as a :py:class:`.rhythm.lib.Timestamp`::

	now = rhythm.lib.now() # UTC

Calendar Representation
-----------------------

A Date can be used to represent the span of the entire day::

	date = rhythm.lib.Date.of(year=1982, month=4, day=17)
	assert date.select('day', 'month') == 17

However, the above actually represents::

	assert date.select('date') == (1982, 5, 18)

Usually, using the `date` keyword is best way to to work with
literal dates::

	assert rhythm.lib.Date.of(date=(1982,5,18)) == date

The calendrical **representation** only takes effect through certain
interfaces::

	ts = rhythm.lib.Timestamp.of(iso="2001-01-01T05:30:01")
	print(repr(ts))
	rhythm.lib.Timestamp.of(iso='2001-01-01T05:30:01.000000')

And from a datetime tuple::

	ts2 = rhythm.lib.Timestamp.of(datetime = (2001, 1, 1, 5, 30, 1, 0))
	assert ts == ts2

rhythm PiTs do not perform calendrical validation; rather, fields with excess
values overflow onto larger units. This is similar to how MySQL handles
overflow. For rhythm, this choice is deliberate and the user is expected to
perform any desired validation::

	pit = rhythm.lib.Date.of(date=(1982,5,0))

The assigned `pit` now points to the last day of the month preceding the fifth
month in the year 1982. This kind of wrapping allows rhythm users to *quickly*
perform some of the most difficult datetime math.

Datetime Math
-------------

rhythm can easily answer questions like, "What was third weekend of the fifth
month of last year?"::

	pit = rhythm.lib.now()
	pit = pit.update('day', 0, 'month') # set to the first day to avoid overflow
	pit = pit.rollback(year=1) # subtract one gregorian year
	pit = pit.update('month', 5-1, 'year') # set to the fifth month
	pit = pit.update('day', 6, 'week') # set to the weekend of the week
	pit = pit.elapse(week = 2)

Things can get a little more interesting when asking, "What is the
last weekend of the month?". It's not a problem::

	# move the beginning of month (to avoid possible day overflow)
	pit = rhythm.lib.now().update('day', 0, 'month')
	# to the next month and then to the end of the previous
	pit = pit.elapse(month = 1).update('day', -1, 'month') # move to the end of the month.
	# 0 is the beginning of the week, so -1 is the end of the prior week.
	pit = pit.update('day', -1, 'week')

On day overflow, the following illustrates the effect::

	# working with a leap year
	pit = rhythm.lib.Timestamp.of(iso='2012-01-31T18:55:33.946259')
	pit.elapse(month=1)
	rhythm.lib.Timestamp.of(iso='2012-03-02T18:55:33.946259')

Month arithmetic does not lose days in order to align the edge of a month.
In order to keep overflow from causing invalid calculations, adjust to the
beginning of the month.

Things can get even more interesting when asking,
"What is the second to last Thursday of the month". Questions like this require
alignment in order to be answered::

	pit = rhythm.lib.now()
	pit = pit.update('day', 0, 'month') # let's say this month
	# but we need the end of the month
	pit = pit.elapse(month=1)
	pit = pit.update('day', -1, 'month') # set to the first day
	# And now something that will appear almost magical if
	# you haven't used a datetime package with a similar feature.
	pit = pit.update('day', 0, 'week', align=-4) # last thursday of month
	pit = pit.rollback(week=1) # second to last

Essentially, alignment allows Thursdays to be seen as the first day of the
week, warranting that the day field will stay the same or be subtracted when
set to zero. This is why the day is set to the last day of the month, in case
the Thursday is the last day of the month, and with proper alignment the first
day of the re-aligned week.

Clocks
------

:py:func:`.rhythm.lib.now` provides quick and easy access to "demotic time", UTC
wall clock. However, rhythm provides clock based devices for processes with
monotonic requirements for things like rate limiting, polling timeouts, and
simple execution-time measures.

Measuring the execution time of a code block is easy with a rhythm stopwatch::

	def work():
		pass

	with rhythm.lib.clock.stopwatch() as snapshot:
		work()

	print(snapshot())
	print(snapshot())


.. note:: Considering the overhead involved with instantiating a
          :py:class:`.rhythm.lib.Timestamp` instance, measuring
          execution with the high-level clock interfaces may
          not be appropriate or may require some adjustments
          accounting for the overhead.


The current runtime of a stopwatch can be accessed within the block as well.
However, once the block exits, the stopwatch will stop tracking elapsed time.

Deltas and meters provide a means to track the change in, monotonic, time::

	for measure_since_last_iteration in rhythm.lib.clock.delta():
		pass

Meters are like deltas, but provide the *total* measurement::

	for measure_since_first_iteration in rhythm.lib.clock.meter():
		pass

Time Zones
----------

Time zone adjustments are supported by zone objects::

	pit = rhythm.lib.now()
	tz = rhythm.lib.zone('America/Los_Angeles')
	local_pit = tz.localize(pit)
	print(local_pit.select('iso'))
"""
__pkg_bottom__ = True
