import os
from .. import kernel

def test_sleeper(test):
	s = kernel.Sleeper()
	s.frequency = 100
	s.remainder = 100
	x = next(s)
	test/x >= 100

	s.remainder = 400
	s.disturb()
	x = next(s)
	test/x == 0

	# show retention of all disturbs
	s.remainder = 50
	s.disturb()
	s.disturb()
	s.disturb()
	test/next(s) == 0
	test/next(s) == 0
	test/next(s) == 0
	test/next(s) >= 50

def test_fork_monotonic(test):
	c = kernel.Chronometer()
	first = next(c)
	first = next(c)
	pid = os.fork()
	if pid == 0:
		second = next(c)
		if second is None or second < first:
			os._exit(13)
		else:
			os._exit(0)
	else:
		pid, code = os.waitpid(pid, 0)

	test/os.WEXITSTATUS(code) == 0 # if 13, Chronometer state did not persist across fork

if __name__ == '__main__':
	import sys; from ...dev import libtest
	libtest.execute(sys.modules[__name__])
