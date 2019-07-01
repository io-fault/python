from .. import library
from .. import views
from . import mock

def test_now(test):
	test.isinstance(library.now(), library.Timestamp)

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

def test_zone(test):
	"""
	# Presumes that Alaska is ~-10 and Japan is ~+10.
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

	# XXX: assuming LA zone consistency. fix with a contrived zone.Zone() instance.
	test/list(library.zone('America/Los_Angeles').slice(start, stop)) == [
		(library.Timestamp.of(iso='2005-10-30T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std'))),
		(library.Timestamp.of(iso='2006-04-02T10:00:00.000000000'),
			views.Zone.Offset((-25200, 'PDT', 'dst'))),
		(library.Timestamp.of(iso='2006-10-29T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std'))),
		(library.Timestamp.of(iso='2007-03-11T10:00:00.000000000'),
			views.Zone.Offset((-25200, 'PDT', 'dst'))),
		(library.Timestamp.of(iso='2007-11-04T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std')))
	]
	test/list(library.zone('MST').slice(start, stop)) == []

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
