"""
# Check earth based units (days).
"""
import itertools
from ...time import earth
from ...time import types

from_units_data = [
	types.Date.Measure(-1),
	types.Date.Measure(0),
	types.Date.Measure(0),
	types.Date.Measure(0),
	types.Date.Measure(0),
	types.Date.Measure(0),
	types.Date.Measure(1),
]

def check_from_units(test, samples):
	for u, s in zip(from_units_data, samples):
		nu = types.Date.Measure(s)
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
