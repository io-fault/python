from .. import library
from .. import types

def test_business_week(test):
	expected = [
		types.Date.of(iso="2009-02-16T3:45:15.0"),
		types.Date.of(iso="2009-02-17T3:45:15.0"),
		types.Date.of(iso="2009-02-18T3:45:15.0"),
		types.Date.of(iso="2009-02-19T3:45:15.0"),
		types.Date.of(iso="2009-02-20T3:45:15.0"),
	]
	test/expected == library.business_week(library.Date.of(iso="2009-02-15T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-16T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-17T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-18T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-19T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-20T3:45:15.0"))
	test/expected == library.business_week(library.Date.of(iso="2009-02-21T3:45:15.0"))

def test_field_delta(test):
	R = (lambda x,y,z: (types.Segment((x,y)).points(z)))

	ts = library.Timestamp.of(year=3000,hour=3,minute=59,second=59)
	test/list(R(*library.field_delta('minute', ts, ts.elapse(second=3)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0)
	]

	test/list(R(*library.field_delta('second', ts, ts.elapse(second=3)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=1),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=2),
	]

	test/list(R(*library.field_delta('second', ts, ts.elapse(second=4)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=1),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=2),
		library.Timestamp.of(year=3000,hour=4,minute=0,second=3),
	]

	test/list(R(*library.field_delta('hour', ts, ts.elapse(second=1)))) == [
		library.Timestamp.of(year=3000,hour=4,minute=0,second=0),
	]

	# backwards field_delta
	ts = library.Timestamp.of(year=3000,hour=4,minute=0,second=0)

	test/list(R(*library.field_delta('minute', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59)
	]

	test/list(R(*library.field_delta('second', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59,second=59),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=58),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=57),
	]

	test/list(R(*library.field_delta('second', ts, ts.rollback(second=3)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=59,second=59),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=58),
		library.Timestamp.of(year=3000,hour=3,minute=59,second=57),
	]

	test/list(R(*library.field_delta('hour', ts, ts.rollback(second=1)))) == [
		library.Timestamp.of(year=3000,hour=3,minute=0,second=0),
	]

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
