from .. import library as libtime
from .. import rate as module
from .mock import Chronometer

class SomeObject(object):
	pass

def test_Radar_split(test):
	# zero split, zero data. unless you have instantaneous flow
	seq = [(2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 0)
	test/[(2, 0)] == list(reversed(pre))
	seq = [(2, 2)]
	pre, suf = module.Radar.split(reversed(seq), 0)
	test/[(0, 0)] == list(reversed(pre))

	# one time unit split

	# instantaneous is always included
	seq = [(2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 1)
	test/seq == list(reversed(pre))
	# exactly half
	seq = [(2, 2)]
	pre, suf = module.Radar.split(reversed(seq), 1)
	test/[(1, 1)] == list(reversed(pre))

	# large units outside of split
	seq = [(10000, 0), (0, 1), (2, 1), (2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 1)
	test/[(0, 0), (2, 1), (2, 0)] == list(reversed(pre))

	# perfectly adjacent instantaneous units will get consumed
	seq = [(10000, 0), (0, 1), (2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 1)
	test/[(10000, 0), (0, 1), (2, 0)] == list(reversed(pre))

	# adjacent, but the overlapping split is zero, so the trailing units is 0
	seq = [(10000, 1), (0, 1), (2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 1)
	test/[(0, 0), (0, 1), (2, 0)] == list(reversed(pre))

	# cut the tail in half
	seq = [(10000, 2), (0, 1), (2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 2)
	test/[(5000, 1), (0, 1), (2, 0)] == list(reversed(pre))

	# validate that the remainder is being ignored.
	seq = [(5, 0), (10000, 2), (0, 1), (2, 0)]
	pre, suf = module.Radar.split(reversed(seq), 2)
	test/[(5000, 1), (0, 1), (2, 0)] == list(reversed(pre))

def test_Radar_sums(test):
	seq = []
	sums = module.Radar.sums(seq)
	test/(0, 0) == sums

	seq = [(0, 0)]
	sums = module.Radar.sums(seq)
	test/(0, 0) == sums

	seq = [(1, 0)]
	sums = module.Radar.sums(seq)
	test/(1, 0) == sums

	seq = [(1, 1), (1, 0)]
	sums = module.Radar.sums(seq)
	test/(2, 1) == sums

	seq = [(1, 1), (1, 1)]
	sums = module.Radar.sums(seq)
	test/(2, 2) == sums

	seq = [(0, 0), (1, 1), (1, 1)]
	sums = module.Radar.sums(seq)
	test/(2, 2) == sums

	seq = [(0, 0), (1, 1), (1, 1)]
	sums = module.Radar.sums(seq)
	test/(2, 2) == sums

def test_Radar_implicit_forget(test):
	"""
	# This test can fail in cases where the object
	# is still, somehow, alive.

	# It looks pretty consistent with respect to python3,
	# but I imagine implementation differences can change things.
	"""
	R = module.Radar(Chronometer = Chronometer)
	a = SomeObject()
	test/R.forget(a) == None
	R.track(a, 0)
	del a
	import gc
	gc.collect()
	test/len(R.tracking) == 0

def test_Radar_explicit_forget(test):
	R = module.Radar(Chronometer = Chronometer)
	a = SomeObject()
	test/R.forget(a) == None
	R.track(a, 0)
	test/R.forget(a) != None

def test_Radar(test):
	"""
	# Test most features of the Radar class.
	"""
	R = module.Radar(Chronometer = Chronometer)
	test/len(R.tracking) == 0
	a = SomeObject()

	update = Chronometer.set
	update(1)
	pair = R.track(a, 0)

	test/pair == R.tracking[a]

	# detects that the chronometer was used by Radar
	test/next(pair[0]) == 0

	# validates that there is a flow being tracked
	test/len(R.tracking) == 1

	test/R.rate(a) == (0, libtime.Measure(1))
	update(20)
	R.track(a, 50)
	test/R.rate(a) == (50, libtime.Measure(21))

	# introduce a new flow
	b = SomeObject()
	R.track(b, 0)
	update(100)
	R.track(b, 10)
	# The internal tracks will yield zeros allowing everything to be seen.
	test/R.all(500) == (50+10, (libtime.Measure(21+100), 2))

	# now truncate
	test/R.truncate(a, 100000) == [] # everything fits in window
	test/R.truncate(b, 100000) == [] # everything fits in window

	# time to actually truncate something
	# but first, let's make the u/t more proportional for ease
	update(9)
	R.track(a, 40)

	test/R.rate(a) == (90, libtime.Measure(30))
	##
	# three explicit tracks()'s, three performed by internal cases.
	test/R.collapse(a) == (90, libtime.Measure(30))
	# should be the same
	test/R.rate(a) == (90, libtime.Measure(30))

	# truncate a third of the time
	test/R.truncate(a, 20) == [(30, 10)]

	# now, collapse b...don't bother checking the count
	R.collapse(b)
	# and check the overall
	test/R.rate(a) == (60, libtime.Measure(20))
	test/R.rate(b) == (10, libtime.Measure(100))
	# two flows, last 10 time units (nanoseconds)
	test/R.all(10) == (30+1, (libtime.Measure(10+10), 2))
	# now, truncate b more so the effect can be perceived via overall
	R.truncate(b, 0)
	test/R.all(10) == (30, (libtime.Measure(10), 2))

def test_Radar_collapse_window(test):
	"""
	# The test_Radar function was written before these features
	# existed. Rather than change that function, test the features
	# independently
	"""
	R = module.Radar(Chronometer = Chronometer)
	update = Chronometer.set

	test/len(R.tracking) == 0
	a = SomeObject()

	# couple records
	R.track(a, 0)
	R.track(a, 0)

	update(100)
	R.track(a, 100)

	update(100)
	R.track(a, 100)

	update(100)
	R.track(a, 100)

	# windowed rate
	test/R.rate(a, 100) == (100, libtime.Measure(100))

	# collapse to a window
	test/R.collapse(a, 50) == (250, libtime.Measure(250))
	test/len(R.tracking[a][1]) == len(range(3))
	# rate should be consistent; no info loss
	test/R.rate(a, 100) == (100, libtime.Measure(100))
	test/R.rate(a, 300) == (300, libtime.Measure(300))
	test/R.rate(a) == (300, libtime.Measure(300))

def test_Radar_zero(test):
	"""
	# Validate that zero destroys the updated time.
	"""
	R = module.Radar(Chronometer = Chronometer)
	update = Chronometer.set

	test/len(R.tracking) == 0
	a = SomeObject()

	# couple records
	update(0)
	R.track(a, 0)
	test/R.rate(a, 100) == (0, libtime.Measure(0))

	update(10)
	test/R.zero(a) == libtime.Measure(10)

	update(0)
	R.track(a, 0)
	test/R.rate(a, 100) == (0, libtime.Measure(0))


def test_Spec_recoverable(test):
	# given a window, validate whether or not it is
	# possible to meet the minimum rate given a maximum
	spec = module.Specification((100, 150, 8))

	# no time left
	test/spec.recoverable(100000, 0) == False

	test/spec.recoverable(0, 1) == False
	test/spec.recoverable(90, 2) == True
	test/spec.recoverable(0, 8) == True
	test/spec.recoverable(30, 1) == False
	test/spec.recoverable(30, 4) == False
	test/spec.recoverable(30, 5) == True
	test/spec.recoverable(30, 6) == True
	test/spec.recoverable(60, 4) == True

	# no max, so always true except when the remainder of time is zero.
	spec = module.Specification((100, None, 8))
	test/spec.recoverable(60, 1) == True
	test/spec.recoverable(-200, 1) == True
	test/spec.recoverable(0, 1) == True

def test_Spec_throttle(test):
	# given a window, validate whether or not it is
	# possible to meet the minimum rate given a maximum
	spec = module.Specification((100, 150, 8))

	# no time left
	test/spec.throttle(150) == 0
	test/int(spec.throttle(300)) == 1
	test/int(spec.throttle(600)) == 3
	test/int(spec.throttle(900)) == 5

	# no max, always zero
	spec = module.Specification((100, None, 8))
	test/spec.throttle(150) == 0
	test/spec.throttle(31231231232312313) == 0
	test/spec.throttle(2**64) == 0
	test/spec.throttle(-123) == 0

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
