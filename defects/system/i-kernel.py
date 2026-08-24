import sys
import os
import signal

from ...system import files
from ...system import kernel as module
from .tools import perform_cat

def test_Invocation(test):
	"""
	# Sanity and operations.
	"""
	notreal = module.Invocation("some string", ())
	test.isinstance(notreal, module.Invocation)

	del notreal
	test.garbage()

	environ = module.Invocation("/bin/cat", ("cat", "-",), environ=dict(SOME_ENVIRON_VAR="foo"))

	realish = module.Invocation("/bin/cat", ("cat", "filepath1", "filepath2", "n"*100,))
	del realish
	test.garbage()

def test_Invocation_file_not_found(test):
	"""
	# Validate that a reasonable OSError is raised when the executable doesn't exist.
	"""
	tr = test.exits.enter_context(files.Path.fs_tmpdir())
	r = tr / 'no-such.exe'
	i = module.Invocation(str(r), [str(r)])

	with open(os.devnull) as f:
		invoke = lambda: i(((f.fileno(), 0), (f.fileno(), 1), (f.fileno(), 2)))
		test/FileNotFoundError ^ invoke

def test_Invocation_execute(test):
	# echo data through cat
	stdin = os.pipe()
	stdout = os.pipe()
	stderr = os.pipe()

	catinv = module.Invocation("/bin/cat", ["cat"], environ={})
	pid = catinv(((stdin[0],0), (stdout[1],1), (stderr[1],2)))

	os.close(stdin[0])
	os.close(stdout[1])
	os.close(stderr[1])

	# process launched?
	os.kill(pid, 0) # Check that process exists.

	data = b'data\n'
	out, status = perform_cat([pid], stdin[1], stdout[0], data, stderr[0])
	test/out == data

def test_wait_process_exit_zero(test):
	inv = module.Invocation('/bin/sleep', ["sleep", "0"])
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	test/module.wait_process(pid) == pid
	test.invert/ProcessLookupError ^ (lambda: os.kill(pid, 0))
	test/module.reap_process(pid) == 0
	test/ProcessLookupError ^ (lambda: os.kill(pid, 0))

def test_wait_process_exit_nonzero(test):
	inv = module.Invocation('/usr/bin/false', ["false"])
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	test/module.wait_process(pid) == pid
	test.invert/ProcessLookupError ^ (lambda: os.kill(pid, 0))
	test/module.reap_process(pid) > 0
	test/ProcessLookupError ^ (lambda: os.kill(pid, 0))

def test_reap_running_process(test):
	inv = module.Invocation('/bin/sleep', ["sleep", "8"])
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	# EBUSY
	test/OSError ^ (lambda: module.reap_process(pid))

	# Clean up.
	os.kill(pid, signal.SIGINT)
	test/module.wait_process(pid) == pid
	test.invert/ProcessLookupError ^ (lambda: os.kill(pid, 0))
	test/module.reap_process(pid) == -signal.SIGINT
	test/ProcessLookupError ^ (lambda: os.kill(pid, 0))

def test_wait_process_exit_signal(test):
	inv = module.Invocation('/bin/sleep', ["sleep", "8"])
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	os.kill(pid, signal.SIGTERM)
	test/module.wait_process(pid) == pid
	test.invert/ProcessLookupError ^ (lambda: os.kill(pid, 0))
	test/module.reap_process(pid) == -signal.SIGTERM
	test/ProcessLookupError ^ (lambda: os.kill(pid, 0))

def test_wait_process_next(test):
	inv = module.Invocation('/bin/sleep', ["sleep", "0"])
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	# No parameter. Any child exit.
	test/module.wait_process() == pid

	test.invert/ProcessLookupError ^ (lambda: os.kill(pid, 0))
	test/module.reap_process(pid) == 0
	test/ProcessLookupError ^ (lambda: os.kill(pid, 0))

def test_process_invalid(test):
	# The exact identifier of a running process is required.
	test/ValueError ^ (lambda: module.reap_process(0))
	test/ValueError ^ (lambda: module.reap_process(-1))

	test/TypeError ^ (lambda: module.reap_process("one"))
	test/TypeError ^ (lambda: module.wait_process("one"))
	test/TypeError ^ (lambda: module.test_process("one"))

def test_wait_process_none(test):
	test/ChildProcessError ^ (lambda: module.wait_process())

def test_test_process(test):
	test/module.test_process() == 0
	test/module.test_process(1) == 0

	inv = module.Invocation('/bin/sleep', ["sleep", "8"], set_process_group=True)
	with open(os.devnull) as f:
		dn = f.fileno()
		pid = inv.spawn([(dn,0), (dn,1), (dn,2)])

	test/module.test_process(pid) == pid
	test/module.test_process(-pid) == -pid
	test/module.test_process() == -1

	os.kill(pid, signal.SIGKILL)
	module.wait_process(pid)

	# Questionable inconsistency, but potentially useful to poll for child exits.
	test/module.test_process(-pid) == pid
	test/module.test_process() == pid

	test/module.reap_process(pid) == -9
	test/module.test_process(pid) == 0

def test_Ports_new(test):
	kp = module.Ports(list(range(10)))
	test/list(kp) == list(range(10))

	# Internal list materialization
	kp = module.Ports((range(10)))
	test/list(kp) == list(range(10))

def test_Ports_sequence(test):
	kp = module.Ports.allocate(16)
	test/len(kp) == 16

	# Iterator
	test/list(kp) == [-1 for x in range(16)]

	test/kp[0] == -1
	test/kp[-1] == -1

	# set/get item.
	for x in range(16):
		kp[x] = 10
		test/kp[x] == 10

def test_Ports_overflow(test):
	"""
	# Presumes integer size; failure of this test may not indicate dysfunction.
	"""
	kp = module.Ports.allocate(1)
	test/OverflowError ^ (lambda: kp.__setitem__(0, 0xfffffffffff))
	test/OverflowError ^ (lambda: module.Ports([0xfffffffffff]))
