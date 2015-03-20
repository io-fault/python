"""
"""
import itertools
from .. import abstract

tests = (
	abstract.Tests(libmetric),
)

def test_classification(test, lib):
	test.fail_if_not_subclass(lib.Unit, abstract.Time)
	test.fail_if_not_subclass(lib.Point, abstract.Time)
	test.fail_if_not_subclass(lib.Point, lib.Unit)

def test_Point_contains(test, lib):
	epoch = lib.Point(0)
	test.fail_if_not_in(epoch, epoch)

	pepoch = libmetric.Point(0)
	test.fail_if_not_in(pepoch, epoch)

	post_epoch = lib.Point(1)
	test.fail_if_in(post_epoch, epoch)

	pre_epoch = libmetric.Point(-1)
	test.fail_if_in(pre_epoch, epoch)

def test_arithmetic(test, lib):
	da = libmetric.Unit.from_microseconds(5)
	db = libmetric.Unit.from_microseconds(0)

	# All deltas..
	test.fail_if_not_instance(da + db, libmetric.Unit)
	test.fail_if_not_instance(db + da, libmetric.Unit)

	a = libmetric.Point(5)
	b = libmetric.Point(0)

	test.fail_if_not_instance(a - b, libmetric.Unit)
	test.fail_if_instance(a - b, libmetric.Point) # Should *not* be a Point.
	test.fail_if_not_instance(b - a, libmetric.Unit)
	test.fail_if_instance(b - a, libmetric.Point) # Should *not* be a Point.

	# Adding or substracting a non-point from a Point leaves a Point.
	test.fail_if_not_instance(b + da, libmetric.Point)
	test.fail_if_not_instance(b - da, libmetric.Point)
	test.fail_if_not_instance(da + b, libmetric.Point)
	test.fail_if_not_instance(da - b, libmetric.Point)

	test.fail_if_not_equal(a - b, da)
	test.fail_if_not_equal(a + b, -da) # Inverse difference on Point addition.
	test.fail_if_not_equal(b + da, a)

	test.fail_if_not_equal(a - b, b + a)
	test.fail_if_not_equal(a + b, b - a) # Inverse difference on Point addition.

def test_negation(test, lib):
	d = lib.Unit.units(50)
	nd = -d
	test.fail_if_greater_than(nd, 0)
	test.fail_if_greater_than(0, d)
	test.fail_if_greater_than(nd, d)
	test.fail_if_not_instance(d, libmetric.Unit)
	test.fail_if_not_instance(nd, libmetric.Unit)

def test_invalid_adjustment(test, lib):
	a = lib.Point(5)
	b = lib.Point(0)
	test.fail_if_not_raised(TypeError, lambda: a.adjust(b))
	test.fail_if_not_raised(TypeError, lambda: a.adjust(a))

def test_features(test, lib):
	# coverage/exception check
	t = lib.Point(0)
	str(t)
	repr(t)
