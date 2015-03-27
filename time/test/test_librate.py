from .. import librate

def test_Spec_recoverable(test):
	# given a window, validate whether or not it is
	# possible to meet the minimum rate given a maximum
	spec = librate.Specification((100, 150, 8))

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
	spec = librate.Specification((100, None, 8))
	test/spec.recoverable(60, 1) == True
	test/spec.recoverable(-200, 1) == True
	test/spec.recoverable(0, 1) == True

def test_Spec_throttle(test):
	# given a window, validate whether or not it is
	# possible to meet the minimum rate given a maximum
	spec = librate.Specification((100, 150, 8))

	# no time left
	test/spec.throttle(150) == 0
	test/int(spec.throttle(300)) == 1
	test/int(spec.throttle(600)) == 3
	test/int(spec.throttle(900)) == 5

	# no max, always zero
	spec = librate.Specification((100, None, 8))
	test/spec.throttle(150) == 0
	test/spec.throttle(31231231232312313) == 0
	test/spec.throttle(2**64) == 0
	test/spec.throttle(-123) == 0

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
