"""
"""
import itertools
from .. import earth
from .. import library as lib

from_units_data = [
	lib.Days(-1),
	lib.Days(0),
	lib.Days(0),
	lib.Days(0),
	lib.Days(0),
	lib.Days(0),
	lib.Days(1),
]

def check_from_units(test, samples):
	for u, s in zip(from_units_data, samples):
		nu = lib.Days(s)
		test/u == nu

def test_from_units_decimal(test):
	import decimal
	T = decimal.Decimal
	return check_from_units(test, [
		T("-1"),
		T("-0.5"),
		T("-0.333333333"),
		T("0"),
		T("0.33333333"),
		T("0.5"),
		T("1"),
	])

def test_from_units_fraction(test):
	import fractions
	T = fractions.Fraction
	return check_from_units(test, [
		-T(1,1),
		-T(1,2),
		-T(1,3),
		T(0,1),
		T(1,3),
		T(1,2),
		T(1,1),
	])

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
