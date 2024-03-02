import os

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
	i = module.Invocation(str(r), ())

	with open(os.devnull) as f:
		invoke = lambda: i(((f.fileno(), 0), (f.fileno(), 1), (f.fileno(), 2)))
		test/FileNotFoundError ^ invoke

def test_Invocation_execute(test):
	# echo data through cat
	stdin = os.pipe()
	stdout = os.pipe()
	stderr = os.pipe()

	catinv = module.Invocation("/bin/cat", (), environ={})
	pid = catinv(((stdin[0],0), (stdout[1],1), (stderr[1],2)))

	os.close(stdin[0])
	os.close(stdout[1])
	os.close(stderr[1])

	# process launched?
	os.kill(pid, 0) # Check that process exists.

	data = b'data\n'
	out, status = perform_cat([pid], stdin[1], stdout[0], data, stderr[0])
	test/out == data

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
