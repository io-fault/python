"""
rhythm.test.test_system
"""
import concur.libprocess
from .. import system

def test_fork_monotonic(test):
	c = system.Chronometer()
	first = next(c)
	first = next(c)
	ref = concur.libprocess.execute(c.__next__)
	res = concur.libprocess.yields(ref)
	test/res > first

if __name__ == '__main__':
	from dev import libtest; libtest.execmodule()
