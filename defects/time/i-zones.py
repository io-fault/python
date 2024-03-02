from ...time import types
from ...time import views
from ...time import system

zone = (lambda x: views.Zone.open(system._unix, x))

def test_zone_data(test):
	"""
	# Presumes that Alaska is ~-10 and Japan is ~+10.
	"""
	today = 'America/Anchorage'
	tomorrow = 'Japan'
	now = system.utc()
	# need to work with the end of the day
	end_of_day = now.update('hour', 23, 'day')

	anchorage_zone = zone(today)
	japan_zone = zone(tomorrow)

	# get the zone offsets according to the end of the day
	anchorage_pit, this_offset = anchorage_zone.localize(now)
	japan_pit, next_offset = japan_zone.localize(now)

	today = types.Date.of(end_of_day, this_offset)
	tomorrow = types.Date.of(end_of_day, next_offset)

	test/today == tomorrow.elapse(day=-1)

def test_zone_dst_offset(test):
	# if this test fails, it *may* be due to timezone database changes
	at = types.Timestamp.of(iso='2019-11-03T09:00:00.000000000')
	before = at.rollback(second=1)
	after = at.elapse(second=1)

	la_zone = zone('America/Los_Angeles')

	local_at_pit, at_offset = la_zone.localize(at)
	local_before_pit, before_offset = la_zone.localize(before)
	local_after_pit, after_offset = la_zone.localize(after)

	test/before_offset.is_dst == True
	test/at_offset.is_dst == False
	test/after_offset.is_dst == False

def test_zone_default_only(test):
	z = zone('MST')
	start = types.Timestamp.of(iso='2006-01-03T09:00:00.000000000')
	pits = [start.elapse(month=i) for i in range(3*12)]

	s = set()
	for x in pits:
		s.add(z.find(x))
	test/len(s) == 1

def test_zone_normalize(test):
	# at a transition point.
	at = types.Timestamp.of(iso='2019-11-03T09:00:00.000000000')

	z = zone('America/Los_Angeles')

	at, o = z.localize(at)
	test/o.is_dst == False

	before = at.rollback(second=1)

	# normalization of `before` should result in a recognized transition
	n_pit, n_offset = z.normalize(o, before)
	test/n_offset != o

def test_zone_slice(test):
	start = types.Timestamp.of(iso='2006-01-03T09:00:00.000000000')
	stop = types.Timestamp.of(iso='2007-12-03T09:00:00.000000000')

	# XXX: assuming LA zone consistency. fix with a contrived zone.Zone() instance.
	test/list(zone('America/Los_Angeles').slice(start, stop)) == [
		(types.Timestamp.of(iso='2005-10-30T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std'))),
		(types.Timestamp.of(iso='2006-04-02T10:00:00.000000000'),
			views.Zone.Offset((-25200, 'PDT', 'dst'))),
		(types.Timestamp.of(iso='2006-10-29T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std'))),
		(types.Timestamp.of(iso='2007-03-11T10:00:00.000000000'),
			views.Zone.Offset((-25200, 'PDT', 'dst'))),
		(types.Timestamp.of(iso='2007-11-04T09:00:00.000000000'),
			views.Zone.Offset((-28800, 'PST', 'std')))
	]
	test/list(zone('MST').slice(start, stop)) == []
