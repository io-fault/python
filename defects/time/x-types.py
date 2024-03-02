import fractions
from ...time import types as module

def test_month_spectrum(test):
	start = module.Timestamp.of(year=1600, month=0, day=0)
	end = module.Timestamp.of(year=2000, month=0, day=0)

	t = start
	while t < end:
		test/t.select('day', 'month') == 0
		n = t.elapse(month=1)
		test/n != t
		test/n >= t
		t = n

	t = end
	while t > start:
		test/t.select('day', 'month') == 0
		n=t.rollback(month=1)
		test/n != t
		test/t >= n
		t = n
