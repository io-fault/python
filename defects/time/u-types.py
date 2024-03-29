import fractions
from ...time import types as module

def test_classes(test):
	pointtypes = [module.Timestamp, module.Date]

	# Check distinct inheritance lines.
	for A in pointtypes:
		B = A.Measure
		with test/test.Absurdity as exc:
			test.issubclass(A, B)

		with test/test.Absurdity as exc:
			test.issubclass(B, A)

def test_select(test):
	"""
	# - &module.select
	"""
	test.issubclass(module.select('hour'), module.Measure)
	test.issubclass(module.select('minute'), module.Measure)
	test.issubclass(module.select('second'), module.Measure)

	test.issubclass(module.select('month'), module.Months)
	test.issubclass(module.select('year'), module.Months)

	test.issubclass(module.select('day'), module.Date.Measure)

def test_instants(test):
	ts = module.Timestamp(0)
	secs = module.Measure(0)
	# no adjustments in __new__
	test/ts == secs

def test_ratios(test):
	test/1000000 == module.Context.compose('second', 'microsecond')
	test/fractions.Fraction(1,1000000) == module.Context.compose('microsecond', 'second')

def test_of_Measure(test):
	mult = int(module.Measure.of(second=1))
	ts = module.Measure.of(second = 20)
	test/ts.start == module.Measure.of()

	test/ts == 20 * mult
	ts = module.Measure.of(second = -20)
	test/ts == -20 * mult
	ts = module.Measure.of(day = 1)
	test/ts == 24 * 60 * 60 * mult
	# multiple fields
	ts = module.Measure.of(day = 1, second = 20)
	test/ts == (24 * 60 * 60 * mult) + (20 * mult)
	# and more
	ts = module.Measure.of(day = 1, minute = 2, second = 20)
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
		module.Measure.unit: 111,
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
	test/total == module.Measure.of(**units)

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
	test/19218117121211121211121211212123000 == module.Measure.of(**units)

def test_of_months(test):
	us = module.Measure.of(month=5)
	d = module.Date.Measure.of(month=5)
	m = module.Months.of(day = d)
	test/int(m) == 5

def test_of_iso(test):
	isostr = "1778-06-01T20:21:22.23"
	ts = module.Timestamp.of(iso=isostr)
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
	isod = module.Date.of(iso=isostr)
	d = module.Date.of(year = 1999, month = 0, day = 0)
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
		ts = module.Timestamp.of(iso=iso)
		if should_wrap:
			test/iso != ts.select('iso')
		else:
			test/iso == ts.select('iso')

def test_of_relative(test):
	ts = module.Timestamp.of(iso="2000-01-00T12:45:00")
	test/ts.select('year') == 1999
	test/ts.select('month', 'year') == 11
	test/ts.select('day', 'month') == 30
	test/ts.select('date') == (1999,12,31)
	test/ts.select('datetime') == (1999,12,31,12,45,0)

def test_date_contains(test):
	d = module.Date.of(year=2000,month=6,day=4)
	p = module.Timestamp.of(year=2000,month=6,day=3,hour=3,minute=23,second=1)
	p in test//d
	d in test//p

	# like day now
	d = module.Date.of(year=2000,month=6,day=3)
	p in test/d

	d in test//p

def test_part_datetime(test):
	# Presuming the datum in this test.
	# Remove or rework if desired.
	t = module.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0,))
	test/0 == t
	t = module.Timestamp(module.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0)) + 1)
	test/1 == t
	t = module.Timestamp(module.Timestamp.of(datetime=(2000, 1, 2, 0, 0, 0)) - 1)
	test/-1 == t

def test_relative_times(test):
	previous_month = module.Timestamp.of(
		datetime=(2000, 0, 1, 0, 0, 0)
	)
	rprevious_month = module.Timestamp.of(
		datetime=(1999, 12, 1, 0, 0, 0)
	)
	test/previous_month == rprevious_month

	previous_day = module.Timestamp.of(
		datetime=(2000, 1, 0, 0, 0, 0)
	)
	rprevious_day = module.Timestamp.of(
		datetime=(1999, 12, 31, 0, 0, 0)
	)
	test/previous_day == rprevious_day

def test_Timestamp_select(test):
	ts = module.Timestamp.of(iso="1599-03-02T03:23:10.003211")
	test/3 == ts.select('hour', 'day')
	test/10 == ts.select('second', 'minute')
	test/3211 == ts.select('microsecond', 'second')
	test/23 == ts.select('minute', 'hour')

	test/1 == ts.select('day', 'month')
	test/2 == ts.select('month', 'year')
	test/1599 == ts.select('year')
	test/99 == ts.select('year', 'century')

def test_Timestamp_update(test):
	ts = module.Timestamp.of(iso="1599-03-02T03:23:10.003211")
	test/ts.update('month', 0, 'year') == module.Timestamp.of(iso="1599-01-02T03:23:10.003211")
	test/ts.update('month', 11, 'year') == module.Timestamp.of(iso="1599-12-02T03:23:10.003211")
	test/ts.update('month', 5, 'year') == module.Timestamp.of(iso="1599-6-02T03:23:10.003211")

def test_date(test):
	ts = module.Timestamp.of(iso="1825-01-15T3:45:01.021344")
	d = module.Date.of(ts)
	ts in test/d

def test_truncate(test):
	samples = [
		(module.Timestamp.of(iso="2000-03-18T13:34:59.999888777"), [
			('week', module.Timestamp.of(iso="2000-03-12T00:00:00.0")),
		]),
		(module.Timestamp.of(iso="2000-03-19T13:34:59.999888777"), [
			('week', module.Timestamp.of(iso="2000-03-19T00:00:00.0")),
		]),
		(module.Timestamp.of(iso="1923-04-18T13:34:59.999888777"), [
			('second', module.Timestamp.of(iso="1923-04-18T13:34:59.000")),
			('minute', module.Timestamp.of(iso="1923-04-18T13:34:00.0")),
			('hour', module.Timestamp.of(iso="1923-04-18T13:00:00.0")),
			('day', module.Timestamp.of(iso="1923-04-18T00:00:00.0")),
			('week', module.Timestamp.of(iso="1923-04-15T00:00:00.0")),
			('month', module.Timestamp.of(iso="1923-04-01")),
			('year', module.Timestamp.of(iso="1923-01-01")),
		]),
	]

	for (ts, cases) in samples:
		for (unit, result) in cases:
			truncd = ts.truncate(unit)
			test/truncd == result

def test_measure_method(test):
	old = module.Timestamp.of(iso="1900-01-01T00:00:00")
	new = module.Timestamp.of(iso="1900-01-11T00:00:00")
	test/old.measure(new) == module.Measure.of(day=10)
	test/new.measure(old) == module.Measure.of(day=-10)

def test_rollback(test):
	ts = module.Timestamp.of(iso="1982-05-18T00:00:00")
	test/ts.measure(ts.rollback(minute=5)) == ts.Measure.of(minute=-5)

def test_timeofday_select(test):
	zero = module.Timestamp(0)
	test/(0, 0, 0) == zero.select('timeofday')
	ts = module.Timestamp.of(iso="1812-01-01T03:45:02")
	test/(3, 45, 2) == ts.select('timeofday')

	ts = module.Timestamp.of(iso="1825-01-15T3:45:01.021344")
	hour, minute, second = ts.select('timeofday')
	test/hour == 3
	test/minute == 45
	test/second == 1

def test_align(test):
	"""
	# The most important use of alignment is for finding the n-th
	# since the first or last of a month.
	"""
	def select_last_thurs(ts):
		ts = ts.elapse(month=1)
		ts = ts.update('day', -1, 'month')
		ts = ts.update('day', 0, 'week', align=-4)
		return ts
	ts = module.Timestamp.of(iso="2010-02-08T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 2, 25)
	ts = module.Timestamp.of(iso="2010-01-09T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 1, 28)
	ts = module.Timestamp.of(iso="2010-09-14T12:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 9, 30)
	ts = module.Timestamp.of(iso="2010-03-21T13:30:00")
	test/select_last_thurs(ts).select('date') == (2010, 3, 25)

def test_unix(test):
	unix_epoch = module.Timestamp.of(iso="1970-01-01T00:00:00")
	ts = module.Timestamp.of(unix=0)
	test/unix_epoch == ts
	test/ts.select('unix') == 0

def test_hashing(test):
	us0 = module.Measure(0)
	ts0 = module.Timestamp(0)
	ds0 = module.Date.Measure(0)
	dt0 = module.Date(0)
	M0 = module.Months(0)
	d = {0:'foo'}
	d[us0] = 'us'
	d[ts0] = 'ts'
	d[ds0] = 'ds'
	d[dt0] = 'dt'
	d[M0] = 'M'
	test/1 == len(d)

def test_subseconds(test):
	val = module.Measure.of(second=1, subsecond=0.5)
	test/val == module.Measure.of(centisecond=150)
	test/float(val.select('subsecond')) == 0.5

def test_Months_elapse(test):
	m = module.Months(1)
	ts = module.Timestamp.of(date=(2000,2,1))
	test/ts.elapse(m) == module.Timestamp.of(date=(2000,3,1))
	test/ts.rollback(m) == module.Timestamp.of(date=(2000,1,1))

def test_indefinite_comparisons(test):
	from ...time.constants import never, whenever, always

	test/True == never.follows(always)
	test/True == never.follows(whenever)

	test/True == always.precedes(never)
	test/True == always.precedes(whenever)

	test/True == whenever.follows(always)
	test/True == whenever.precedes(never)

def test_indefinite_definite_comparisons(test):
	from ...time.constants import never, whenever, always

	ts = module.Timestamp.of(iso="2000-01-01T00:00:00")
	test/True == never.follows(ts)
	test/True == always.precedes(ts)

	test/True == ts.follows(always)
	test/True == ts.precedes(never)

def test_representations(test):
	test/repr(module.Date.of(year=2000)) == "(time.date@'2000-01-01')"
	test/repr(module.Date.of(year=2000, month=1, day=2)) == "(time.date@'2000-02-03')"

	zero = 'T00:00:00.0'
	test/repr(module.Timestamp.of(year=2000)) == f"(time.stamp@'2000-01-01{zero}')"
	test/repr(module.Timestamp.of(year=2000, month=1, day=2)) == f"(time.stamp@'2000-02-03{zero}')"

	test/repr(module.Measure.of(day=3)) == "(time.measure@'3d')"
	test/repr(module.Measure.of(day=3, second=2)) == "(time.measure@'3d.2s')"
	test/repr(module.Measure.of(second=2, nanosecond=20)) == "(time.measure@'2s.20ns')"
