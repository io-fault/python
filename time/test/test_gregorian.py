"""
"""
import itertools
from .. import gregorian

def test_year_is_leap(test):
	# hand picked years
	test/True == gregorian.year_is_leap(2000)
	test/False == gregorian.year_is_leap(1999)
	test/False == gregorian.year_is_leap(1998)
	test/False == gregorian.year_is_leap(1997)
	test/True == gregorian.year_is_leap(1996)
	test/True == gregorian.year_is_leap(1600)
	test/True == gregorian.year_is_leap(1604)
	test/True == gregorian.year_is_leap(1200)
	test/False == gregorian.year_is_leap(1900)
	test/False == gregorian.year_is_leap(1800)
	test/False == gregorian.year_is_leap(1700)
	test/True == gregorian.year_is_leap(1704)
	for x, i in zip(itertools.cycle((True, False, False, False)), range(1600, 1700)):
		test/x == gregorian.year_is_leap(i)

mfd_io_samples = [
	(0, 0), # first day of jan
	(1, 0),
	(2, 0),
	(30, 0), # last day of january
	(31, 1), # first day of feb
	((365*4) + 1, (12 * 4)),
	# century
	(((365*4) + 1) * 25, (12 * 4 * 25)),
	# next century
	((((365*4) + 1) * 25) + 30, (12 * 4 * 25)),
	((((365*4) + 1) * 25) + 31, (12 * 4 * 25) + 1),
	# now the skipped leap of the second century in the cycle.
	((((365*4) + 1) * 25) + 31 + 27, (12 * 4 * 25) + 1),
	((((365*4) + 1) * 25) + 31 + 28, (12 * 4 * 25) + 2),
	# now to the following four-year cycle to check for leap presence
	((((365*4) + 1) * 26) - 1 + 31 + 28, (12 * 4 * 26) + 1),
	((((365*4) + 1) * 26) - 1 + 31 + 29, (12 * 4 * 26) + 2),
]

def test_month_from_days(test):
	for x in mfd_io_samples:
		days, md = x
		test/md == gregorian.month_from_days(days)

def test_mfd_alignment(test):
	for x in mfd_io_samples:
		days, md = x
		# mfd was proved in a prior test.
		# valid
		m = gregorian.month_from_days(days)
		d = gregorian.days_from_month(md)
		test/days >= d
		firstof = gregorian.month_from_days(d)
		test/m == firstof

def test_scan_months(test):
	"""
	Shows month_from_days aligning at the start of the month.
	"""
	month = (12 * 400) - 1
	while month > 0:
		days = gregorian.days_from_month(month)
		next = gregorian.month_from_days(days - 1)
		test/next == month - 1
		month = next

##
# Takes a bit more work as DFM returns month-1 with the total day remainder.
dfm_io_samples = [
	(0, 0),
	(1, 31),
	(2, 60),
]

def test_days_from_month(test):
	for x in dfm_io_samples:
		month, days = x
		test/days == gregorian.days_from_month(month)

date_io_samples = [
	# whole cycle checks
	((2400,1,1), 6 * gregorian.days_in_cycle),
	((2000,1,1), 5 * gregorian.days_in_cycle),
	((1600,1,1), 4 * gregorian.days_in_cycle),
	((1200,1,1), 3 * gregorian.days_in_cycle),
	((800,1,1), 2 * gregorian.days_in_cycle),
	((400,1,1), gregorian.days_in_cycle),
	((0,1,1), 0),
	# and one
	((0,1,2), 1),
	# and two
	((400,1,3), 2 + gregorian.days_in_cycle),
]

def test_date_from_days(test):
	for x in date_io_samples:
		date, days = x
		test/date == gregorian.date_from_days(days)

def test_days_from_date(test):
	for x in date_io_samples:
		date, days = x
		test/days == gregorian.days_from_date(date)

if __name__ == '__main__':
	import sys; from ...dev import libtest
	libtest.execute(sys.modules[__name__])
