from .. import lib
from .. import libharm
from . import mock

def test_harmony(test):
	class Chronometer(mock.Chronometer):
		def snapshot(self):
			return self.__next__()
	H = libharm.Harmony(Chronometer = Chronometer)

	test/libharm.Harmony - libharm.Harmony
	test/H / libharm.Harmony

	update = Chronometer.set
	update(0)

	events = [
		(lib.Measure.of(second=1), -1),
		(lib.Measure.of(second=2), -2),
		(lib.Measure.of(second=3), -3),
		(lib.Measure.of(second=3), -3),
	]
	H.put(*events)

	for x in range(10):
		update(0)
		test/H.get() == []

	update(lib.Measure.of(millisecond=500))
	test/[] == H.get()
	update(lib.Measure.of(millisecond=900))
	test/[] == H.get()

	update(lib.Measure.of(millisecond=1000))
	test/[(lib.Measure.of(second=0), events[0][1])] == H.get()

	# show the state change; cheating a bit with a chronometer
	# that can run backwards, but that is why these tests are awesome =)
	update(lib.Measure.of(millisecond=1000))
	test/[] == H.get()

	# still nothing
	update(lib.Measure.of(millisecond=1900))
	test/[] == H.get()

	# show overflow math
	update(lib.Measure.of(millisecond=2100))
	test/[(lib.Measure.of(millisecond=100), events[1][1])] == H.get()

	# duplicate entries are not collapsed
	update(lib.Measure.of(millisecond=3000))
	zero = lib.Measure.of(millisecond=0)
	test/[(zero, events[2][1]), (zero, events[3][1])] == H.get()

	# empty
	update(lib.Measure.of(millisecond=900))
	test/[] == H.get()

def test_harmony_cancel(test):
	# Same tests as above, but with cancellations

	class Chronometer(mock.Chronometer):
		def snapshot(self):
			return self.__next__()
	H = libharm.Harmony(Chronometer = Chronometer)
	update = Chronometer.set
	update(0)

	events = [
		(lib.Measure.of(second=1), -1),
		(lib.Measure.of(second=2), -2),
		(lib.Measure.of(second=3), -3),
		(lib.Measure.of(second=3), -3),
	]
	H.put(*events)

	for x in range(10):
		update(0)
		test/[] == H.get()

	update(lib.Measure.of(millisecond=500))
	test/[] == H.get()
	update(lib.Measure.of(millisecond=900))
	test/[] == H.get()

	update(lib.Measure.of(millisecond=1000))
	test/[(lib.Measure.of(second=0), events[0][1])] == H.get()

	# show the state change; cheating a bit with a chronometer
	# that can run backwards, but that is why these tests are awesome =)
	update(lib.Measure.of(millisecond=1000))
	test/[] == H.get()

	# still nothing
	update(lib.Measure.of(millisecond=1900))
	test/[] == H.get()

	# show cancel effect
	H.cancel(events[-3][1])
	update(lib.Measure.of(millisecond=2100))
	test/[] == H.get()

	update(lib.Measure.of(millisecond=2900))
	test/lib.Measure.of(millisecond=100) == H.period()

	# duplicate entries are not collapsed
	# one is cancelled
	update(lib.Measure.of(millisecond=3000))
	H.cancel(events[-2][1])
	test/H.get() == [(lib.Measure.of(millisecond=0), events[2][1]),]

	update(lib.Measure.of(millisecond=900))
	test/[] == H.get()

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
