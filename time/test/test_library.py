import fractions
from .. import library
from .. import libzone
from . import mock

def test_classes(test):
	test//library.Timestamp - library.Measure
	test//library.Date - library.Days
	test//library.Week - library.Weeks
	test//library.GregorianMonth - library.Months

def test_instants(test):
	ts = library.Timestamp(0)
	secs = library.Measure(0)
	# no adjustments in __new__
	test/ts == secs

def test_ratios(test):
	test/1000000 == library.Context.compose('second', 'microsecond')
	test/fractions.Fraction(1,1000000) == library.Context.compose('microsecond', 'second')

def test_of_Measure(test):
	mult = int(library.Measure.of(second=1))
	ts = library.Measure.of(second = 20)
	test/ts.start == library.Measure.of()

	test/ts == 20 * mult
	ts = library.Measure.of(second = -20)
	test/ts == -20 * mult
	ts = library.Measure.of(day = 1)
	test/ts == 24 * 60 * 60 * mult
	# multiple fields
	ts = library.Measure.of(day = 1, second = 20)
	test/ts == (24 * 60 * 60 * mult) + (20 * mult)
	# and more
	ts = library.Measure.of(day = 1, minute = 2, second = 20)
	test/ts == (24 * 60 * 60 * mult) + (2*60*mult) + (20 * mult)

	# and much more o.O
	units = {
		'week': 1,
		'day': 1,
		'hour': 1,
		'minute': 1,
		'second': 1,
		'megasecond': 1,
		'kilosecond': 1,
		'millisecond': 1,
		'centisecond': 1,
		'decisecond': 1,
		library.Measure.unit: 111,
	}

	total = 111 + mult + (
		(60 * mult) + \
		(60 * 60 * mult) + \
		(24 * 60 * 60 * mult) + \
		(7 * 24 * 60 * 60 * mult) + \
		((10 ** 6) * mult) + \
		((10 ** 3) * mult) + \
		int((10 ** (-3)) / (10 ** (-9))) + \
		int((10 ** (-2)) / (10 ** (-9))) + \
		int((10 ** (-1)) / (10 ** (-9)))
	)
	test/total == library.Measure.of(**units)

	# 1111...
	units = {
		'microsecond': 123,
		'millisecond': 2,
		'centisecond': 1,
		'decisecond': 2,
		'second': 1,
		'decasecond': 1,
		'hectosecond': 2,
		'kilosecond': 121,
		'megasecond': 211,
		'gigasecond': 121,
		'terasecond': 211,
		'petasecond': 121,
		'exasecond': 117,
		'zettasecond': 218,
		'yottasecond': 19
	}
	# The number is the concatenation of the above parts.
	test/19218117121211121211121211212123000 == library.Measure.of(**units)

def test_of_months(test):
	us = library.Measure.of(month=5)
	d = library.Days.of(month=5)
	m = library.Months.of(day = d)
	test/int(m) == 5

def test_of_iso(test):
	isostr = "1778-06-01T20:21:22.23"
	ts = library.Timestamp.of(iso=isostr)
	pts = ts.of(
		year = 1778, month = 5, day = 0,
		hour = 20, minute = 21, second = 22,
		microsecond = 230000)
	test/ts == pts
	test/ts.select('iso') == isostr
	test/pts.select('iso') == isostr
	test/ts.of(iso=ts.select('iso')) == pts

def test_of_iso_date(test):
	isostr = "1999-01-01"
	isod = library.Date.of(iso=isostr)
	d = library.Date.of(year = 1999, month = 0, day = 0)
	test/isod.select('date') == (1999,1,1)
	test/d == isod

leap_samples = [
	(False, "1600-02-29T00:00:00.0"), # shouldnt wrap
	(True, "1601-02-29T00:00:00.0"), # should wrap
	(False, "1604-02-29T00:00:00.0"), # shouldn't wrap
	(True, "1700-02-29T00:00:00.0"), # should wrap
	(True, "1800-02-29T00:00:00.0"), # should wrap
	(True, "1900-02-29T00:00:00.0"), # should wrap
	(False, "2000-02-29T00:00:00.0"), # shouldn't wrap
]

def test_of_leaps(test):
	for should_wrap, iso in leap_samples:
		ts = library.Timestamp.of(iso=iso)
		if should_wrap:
			test/iso != ts.select('iso')
		else:
			test/iso == ts.select('iso')

def test_of_relative(test):
	ts = library.Timestamp.of(iso="2000-01-00T12:45:00")
	test/ts.select('year') == 1999
	test/ts.select('month', 'year') == 11
	test/ts.select('day', 'month') == 30
	test/ts.select('date') == (1999,12,31)
	test/ts.select('datetime') == (1999,12,31,12,45,0)

def test_date_contains(test):
	d = library.Date.of(year=2000,month=6,day=4)
	p = library.Timestamp.of(year=2000,month=6,day=3,hour=3,minute=23,second=1)
	p in test//d
	d in test//p

	# like day now
	d = library.Date.of(year=2000,month=6,day=3)
	p in test/d

	d in test//p

def test_week_contains(test):
	w = library.Week.of(date=(1999,12,30))
	d = library.Date.of(w)
	dts = library.Timestamp.of(d)
	wts = library.Timestamp.of(w)
	w in test/dts
	w in test/wts
	w in test/d
	for x in range(7):
		d.elapse(day=x) in test/w
	# negatives
	d.elapse(day=-1) in test//w
	d.elapse(day=7) in test//w

def test_part_datetime(test):
	# Presuming the datum in this test.
	# Remove or rework if desired.
	t = library.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0,))
	test/0 == t
	t = library.Timestamp(library.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0)) + 1)
	test/1 == t
	t = library.Timestamp(library.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0)) - 1)
	test/-1 == t

def test_relative_times(test):
	previous_month = library.Timestamp.of(
		datetime=(2000, 0, 1, 0, 0, 0)
	)
	rprevious_month = library.Timestamp.of(
		datetime=(1999, 12, 1, 0, 0, 0)
	)
	test/previous_month == rprevious_month

	previous_day = library.Timestamp.of(
		datetime=(2000, 1, 0, 0, 0, 0)
	)
	rprevious_day = library.Timestamp.of(
		datetime=(1999, 12, 31, 0, 0, 0)
	)
	test/previous_day == rprevious_day

def test_lib_select(test):
	ts = library.Timestamp.of(iso="1599-03-02T03:23:10.003211")
	test/3 == library.select.hour.day()(ts)
	test/10 == library.select.second.minute()(ts)
	test/3211 == library.select.microsecond.second()(ts)
	test/23 == library.select.minute.hour()(ts)
	#
	test/1 == library.select.day.month()(ts)
	test/2 == library.select.month.year()(ts)
	test/1599 == library.select.year()(ts)
	test/99 == library.select.year.century()(ts)

def test_lib_update(test):
	ts = library.Timestamp.of(iso="1599-03-02T03:23:10.003211")
	test/ts.update('month', 0, 'year') == library.Timestamp.of(iso="1599-01-02T03:23:10.003211")
	test/ts.update('month', 11, 'year') == library.Timestamp.of(iso="1599-12-02T03:23:10.003211")
	test/ts.update('month', 5, 'year') == library.Timestamp.of(iso="1599-6-02T03:23:10.003211")
	test/ts.update('month', 6, 'year') == library.update.month.year(6)(ts)
	test/ts.update('day', 15, 'month') == library.update.day.month(15)(ts)
	test/ts.update('day', 2, 'week') == library.update.day.week(2)(ts)
	test/ts.update('hour', 23, 'day') == library.update.hour.day(23)(ts)

def test_date(test):
	ts = library.Timestamp.of(iso="1825-01-15T3:45:01.021344")
	d = library.Date.of(ts)
	ts in test/d

def test_truncate(test):
	samples = [
		(library.Timestamp.of(iso="2000-03-18T13:34:59.999888777"), [
			('week', library.Timestamp.of(iso="2000-03-12T00:00:00.0")),
		]),
		(library.Timestamp.of(iso="2000-03-19T13:34:59.999888777"), [
			('week', library.Timestamp.of(iso="2000-03-19T00:00:00.0")),
		]),
		(library.Timestamp.of(iso="1923-04-18T13:34:59.999888777"), [
			('second', library.Timestamp.of(iso="1923-04-18T13:34:59.000")),
			('minute', library.Timestamp.of(iso="1923-04-18T13:34:00.0")),
			('hour', library.Timestamp.of(iso="1923-04-18T13:00:00.0")),
			('day', library.Timestamp.of(iso="1923-04-18T00:00:00.0")),
			('week', library.Timestamp.of(iso="1923-04-15T00:00:00.0")),
			('month', library.Timestamp.of(iso="1923-04-01")),
			('year', library.Timestamp.of(iso="1923-01-01")),
		]),
	]

	for (ts, cases) in samples:
		for (unit, result) in cases:
			truncd = ts.truncate(unit)
			test/truncd == result

def test_measure_method(test):
	old = library.Timestamp.of(iso="1900-01-01T00:00:00")
	new = library.Timestamp.of(iso="1900-01-11T00:00:00")
	test/old.measure(new) == library.Measure.of(day=10)
	test/new.measure(old) == library.Measure.of(day=-10)

def test_rollback(test):
	ts = library.Timestamp.of(iso="1982-05-18T00:00:00")
	test/ts.measure(ts.rollback(minute=5)) == ts.Measure.of(minute=-5)

def test_timeofday_select(test):
	zero = library.Timestamp(0)
	test/(0, 0, 0) == zero.select('timeofday')
	ts = library.Timestamp.of(iso="1812-01-01T03:45:02")
	test/(3, 45, 2) == ts.select('timeofday')

	ts = library.Timestamp.of(iso="1825-01-15T3:45:01.021344")
	hour, minute, second = ts.select('timeofday')
	test/hour == 3
	test/minute == 45
	test/second == 1

def test_align(test):
	"""
	The most important use of alignment is for finding the n-th
	since the first or last of a month.
	"""
	def select_last_thurs(ts):
		ts = ts.elapse(month=1)
		ts = ts.update('day', -1, 'month')
		ts = ts.update('day', 0, 'week', align=-4)
		return ts
	ts = library.Timestamp.of(iso="2010-02-08T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 2, 25)
	ts = library.Timestamp.of(iso="2010-01-09T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 1, 28)
	ts = library.Timestamp.of(iso="2010-09-14T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 9, 30)
	ts = library.Timestamp.of(iso="2010-03-21T13:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 3, 25)

def test_unix(test):
	unix_epoch = library.Timestamp.of(iso="1970-01-01T00:00:00")
	ts = library.Timestamp.of(unix=0)
	test/unix_epoch == ts
	test/unix_epoch == library.unix(0)
	test/ts.select('unix') == 0

def test_hashing(test):
	us0 = library.Measure(0)
	ts0 = library.Timestamp(0)
	ds0 = library.Days(0)
	dt0 = library.Date(0)
	M0 = library.Months(0)
	gm0 = library.GregorianMonth(0)
	d = {0:'foo'}
	d[us0] = 'us'
	d[ts0] = 'ts'
	d[ds0] = 'ds'
	d[dt0] = 'dt'
	d[M0] = 'M'
	d[gm0] = 'GM'
	test/1 == len(d) # wait, really?

def test_now(test):
	test/library.now() / library.Timestamp

def test_business_week(test):
	expected = [
		library.Date.of(iso="2009-02-16T3:45:15.0"),
		library.Date.of(iso="2009-02-17T3:45:15.0"),
		library.Date.of(iso="2009-02-18T3:45:15.0"),
		library.Date.of(iso="2009-02-19T3:45:15.0"),
		library.Date.of(iso="2009-02-20T3:45:15.0"),
	]
	test/expected == library.business_week(library.Date.of(iso="2009-02-15T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-16T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-17T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-18T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-19T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-20T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-21T3:45:15.0"))

def test_subseconds(test):
	val = library.Measure.of(second=1, subsecond=0.5)
	test/val == library.Measure.of(centisecond=150)
	test/float(val.select('subsecond')) == 0.5

def test_clock_features(test):
	clock = library.clock
	test/clock.demotic() / library.Timestamp
	test/clock.monotonic() / library.Measure
	test/clock.sleep(123) / library.Measure

	for x, t in zip(range(3), clock.meter()):
		test/t >= 0
		test/t >= 0
		test/t / library.Measure
	for x, t in zip(range(3), clock.delta()):
		test/t >= 0
		test/t / library.Measure
	with clock.stopwatch() as total:
		pass
	test/total() / library.Measure
	test/total() == total()

	periods = clock.periods(library.Measure.of(subsecond=0.1))
	test/next(periods)[0] == 0 # fragile
	clock.sleep(library.Measure.of(subsecond=0.1))
	test/next(periods)[0] == 1 # fragile
	clock.sleep(library.Measure.of(subsecond=0.2))
	test/next(periods)[0] == 2 # fragile

def test_range(test):
	y2k = library.Timestamp.of(year=2000, month=0, day=0)
	test/[y2k] == list(library.range(
			library.Timestamp.of(year=2000,month=0,day=0),
			library.Timestamp.of(year=2001,month=0,day=0),
			library.Months.of(year=1)
	))

	y2k1 = library.Timestamp.of(year=2001,month=0,day=0)
	test/[y2k, y2k1] == list(library.range(
		library.Timestamp.of(year=2000,month=0,day=0),
		library.Timestamp.of(year=2002,month=0,day=0),
		library.Months.of(year=1)
	))

def test_field_delta(test):
	ts = library.Timestamp.of(year=3000,hour=3,minute=59,second=59)
	test/list(library.range(*library.field_delta('minute', ts, ts.elapse(second=3)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0)
	]

	test/list(library.range(*library.field_delta('second', ts, ts.elapse(second=3)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=1),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=2),
	]

	test/list(library.range(*library.field_delta('second', ts, ts.elapse(second=4)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=1),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=2),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=3),
	]

	test/list(library.range(*library.field_delta('hour', ts, ts.elapse(second=1)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
	]

	# backwards field_delta
	ts = library.Timestamp.of(year=3000,hour=4,minute=0,second=0)

	test/list(library.range(*library.field_delta('minute', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59)
	]

	test/list(library.range(*library.field_delta('second', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59,second=59),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=58),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=57),
	]

	test/list(library.range(*library.field_delta('second', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59,second=59),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=58),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=57),
	]

	test/list(library.range(*library.field_delta('hour', ts, ts.rollback(second=1)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=0,second=0),
	]

def test_Months_elapse(test):
	m = library.Months(1)
	ts = library.Timestamp.of(date=(2000,2,1))
	test/ts.elapse(m) == library.Timestamp.of(date=(2000,3,1))
	test/ts.rollback(m) == library.Timestamp.of(date=(2000,1,1))

def test_month_spectrum(test):
	test.explicit()
	start = library.Timestamp.of(year=1600, month=0, day=0)
	end = library.Timestamp.of(year=2000, month=0, day=0)

	t = start
	while t < end:
		test/t.select('day','month') == 0
		n = t.elapse(month=1)
		test/n != t
		test/n >= t
		t = n

	t = end
	while t > start:
		test/t.select('day','month') == 0
		n=t.rollback(month=1)
		test/n != t
		test/t >= n
		t = n

def test_zone(test):
	"""
	Presumes that Alaska is ~-10 and Japan is ~+10.
	"""
	today = 'America/Anchorage'
	tomorrow = 'Japan'
	now = library.now()
	# need to work with the end of the day
	end_of_day = now.update('hour', 23, 'day')

	anchorage_zone = library.zone(today)
	japan_zone = library.zone(tomorrow)

	# get the zone offsets according to the end of the day
	anchorage_pit, this_offset = anchorage_zone.localize(now)
	japan_pit, next_offset = japan_zone.localize(now)

	today = library.Date.of(end_of_day, this_offset)
	tomorrow = library.Date.of(end_of_day, next_offset)

	test/today == tomorrow.elapse(day=-1)

def test_zone_dst_offset(test):
	# if this test fails, it *may* be due to timezone database changes
	at = library.Timestamp.of(iso='2019-11-03T09:00:00.000000000')
	before = at.rollback(second=1)
	after = at.elapse(second=1)

	la_zone = library.zone('America/Los_Angeles')

	local_at_pit, at_offset = la_zone.localize(at)
	local_before_pit, before_offset = la_zone.localize(before)
	local_after_pit, after_offset = la_zone.localize(after)

	test/before_offset.is_dst == True
	test/at_offset.is_dst == False
	test/after_offset.is_dst == False

def test_zone_default_only(test):
	z = library.zone('MST')
	pits = library.range(
		library.Timestamp.of(iso='2006-01-03T09:00:00.000000000'),
		library.Timestamp.of(iso='2009-01-03T09:00:00.000000000'),
		library.Months.of(month=1)
	)
	s = set()
	for x in pits:
		s.add(z.find(x))
	test/len(s) == 1

def test_zone_normalize(test):
	# at a transition point.
	at = library.Timestamp.of(iso='2019-11-03T09:00:00.000000000')

	z = library.zone('America/Los_Angeles')

	at, o = z.localize(at)
	test/o.is_dst == False

	before = at.rollback(second=1)

	# normalization of `before` should result in a recognized transition
	n_pit, n_offset = z.normalize(o, before)
	test/n_offset != o

def test_zone_slice(test):
	start = library.Timestamp.of(iso='2006-01-03T09:00:00.000000000')
	stop = library.Timestamp.of(iso='2007-12-03T09:00:00.000000000')

	# XXX: assuming LA zone consistency. fix with a contrived libzone.Zone() instance.
	test/list(library.zone('America/Los_Angeles').slice(start, stop)) == [
		(library.Timestamp.of(iso='2005-10-30T09:00:00.000000000'), libzone.Offset((-28800, 'PST', 'std'))),
		(library.Timestamp.of(iso='2006-04-02T10:00:00.000000000'), libzone.Offset((-25200, 'PDT', 'dst'))),
		(library.Timestamp.of(iso='2006-10-29T09:00:00.000000000'), libzone.Offset((-28800, 'PST', 'std'))),
		(library.Timestamp.of(iso='2007-03-11T10:00:00.000000000'), libzone.Offset((-25200, 'PDT', 'dst'))),
		(library.Timestamp.of(iso='2007-11-04T09:00:00.000000000'), libzone.Offset((-28800, 'PST', 'std')))
	]
	test/list(library.zone('MST').slice(start, stop)) == []

def test_indefinite_comparisons(test):
	test/True == library.never.follows(library.genesis)
	test/True == library.never.follows(library.present)

	test/True == library.genesis.precedes(library.never)
	test/True == library.genesis.precedes(library.present)

	test/True == library.present.follows(library.genesis)
	test/True == library.present.precedes(library.never)

def test_indefinite_segments(test):
	# present is *part* of the past and the future according to our definition.
	test/True == (library.present in library.past)
	test/True == (library.present in library.future)
	test/True == (library.present in library.continuum)

	test/True == (library.now().elapse(hour=1) in library.future)
	test/True == (library.now().elapse(hour=-1) in library.past)

	test/False == (library.now().elapse(hour=-1) in library.future)
	test/False == (library.now().elapse(hour=1) in library.past)

def test_indefinite_containment(test):
	start = library.now().elapse(hour=-2)
	end = start.elapse(hour=4)
	present_window = library.Segment((start, end))

	start = library.now().elapse(hour=-2)
	end = start.elapse(hour=1)
	past_window = library.Segment((start, end))

	start = library.now().elapse(hour=1)
	end = start.elapse(hour=1)
	future_window = library.Segment((start, end))

	test/True == (library.present in present_window)
	test/False == (library.present in past_window)
	test/False == (library.present in future_window)

def test_indefinite_definite_comparisons(test):
	ts = library.now()

	test/True == library.never.follows(ts)
	test/True == library.genesis.precedes(ts)

	test/True == ts.follows(library.genesis)
	test/True == ts.precedes(library.never)

	test/True == library.present.follows(ts.elapse(hour=-1))
	test/True == library.present.precedes(ts.elapse(hour=1))

def test_scheduler(test):
	class Chronometer(mock.Chronometer):
		def snapshot(self):
			return self.__next__()
	H = library.Scheduler(Chronometer = Chronometer)

	test/H / library.Scheduler

	update = Chronometer.set
	update(0)

	events = [
		(library.Measure.of(second=1), -1),
		(library.Measure.of(second=2), -2),
		(library.Measure.of(second=3), -3),
		(library.Measure.of(second=3), -3),
	]
	H.put(*events)

	for x in range(10):
		update(0)
		test/H.get() == []

	update(library.Measure.of(millisecond=500))
	test/[] == H.get()
	update(library.Measure.of(millisecond=900))
	test/[] == H.get()

	update(library.Measure.of(millisecond=1000))
	test/[(library.Measure.of(second=0), events[0][1])] == H.get()

	# show the state change; cheating a bit with a chronometer
	# that can run backwards, but that is why these tests are awesome =)
	update(library.Measure.of(millisecond=1000))
	test/[] == H.get()

	# still nothing
	update(library.Measure.of(millisecond=1900))
	test/[] == H.get()

	# show overflow math
	update(library.Measure.of(millisecond=2100))
	test/[(library.Measure.of(millisecond=100), events[1][1])] == H.get()

	# duplicate entries are not collapsed
	update(library.Measure.of(millisecond=3000))
	zero = library.Measure.of(millisecond=0)
	test/[(zero, events[2][1]), (zero, events[3][1])] == H.get()

	# empty
	update(library.Measure.of(millisecond=900))
	test/[] == H.get()

def test_scheduler_cancel(test):
	# Same tests as above, but with cancellations

	class Chronometer(mock.Chronometer):
		def snapshot(self):
			return self.__next__()
	H = library.Scheduler(Chronometer = Chronometer)
	update = Chronometer.set
	update(0)

	events = [
		(library.Measure.of(second=1), -1),
		(library.Measure.of(second=2), -2),
		(library.Measure.of(second=3), -3),
		(library.Measure.of(second=3), -3),
	]
	H.put(*events)

	for x in range(10):
		update(0)
		test/[] == H.get()

	update(library.Measure.of(millisecond=500))
	test/[] == H.get()
	update(library.Measure.of(millisecond=900))
	test/[] == H.get()

	update(library.Measure.of(millisecond=1000))
	test/[(library.Measure.of(second=0), events[0][1])] == H.get()

	# show the state change; cheating a bit with a chronometer
	# that can run backwards, but that is why these tests are awesome =)
	update(library.Measure.of(millisecond=1000))
	test/[] == H.get()

	# still nothing
	update(library.Measure.of(millisecond=1900))
	test/[] == H.get()

	# show cancel effect
	H.cancel(events[-3][1])
	update(library.Measure.of(millisecond=2100))
	test/[] == H.get()

	update(library.Measure.of(millisecond=2900))
	test/library.Measure.of(millisecond=100) == H.period()

	# duplicate entries are not collapsed
	# one is cancelled
	update(library.Measure.of(millisecond=3000))
	H.cancel(events[-2][1])
	test/H.get() == [(library.Measure.of(millisecond=0), events[2][1]),]

	update(library.Measure.of(millisecond=900))
	test/[] == H.get()

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
