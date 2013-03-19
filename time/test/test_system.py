"""
rhythm.test.test_system
"""
import os
from .. import system

def test_fork_monotonic(test):
	c = system.Chronometer()
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
	from dev import libtest; libtest.execmodule()
