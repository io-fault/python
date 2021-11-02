import os
import signal

from .. import process as module
from .. import thread

class Trapped(Exception):
	"""
	# Exception Fixture for test_critical.
	"""
	pass

def test_critical(test):
	"""
	# &.module.critical
	"""
	global Trapped
	test.issubclass(Trapped, Exception) # sanity

	# Check that critical returns.
	# It's only fatal when an exception is raised.
	def return_obj(*args, **kw):
		return (args, kw)
	result = module.critical(None, return_obj, "positional", keyword='value')
	test/result[0] == ("positional",)
	test/result[1] == {"keyword":'value'}

	def raise_trap():
		global Trapped
		raise Trapped("exception")

	raised_called = False
	def raised(replacement):
		nonlocal raised_called
		raised_called = True
		replacement()

	# Interject is not being tested here, so override
	# it to derive the effect that we're looking for.
	original = module.interject
	ctllock = module.__control_lock__
	try:
		module.interject = raised
		l = module.__control_lock__ = thread.amutex()
		l.acquire()
		try:
			module.critical(None, raise_trap)
		except module.Panic as exc:
			test.isinstance(exc.__cause__, Trapped)
		except:
			test.fail("critical did not raise panic")
		else:
			test.fail("critical did not raise panic")
	finally:
		module.interject = original
		module.__control_lock__ = ctllock

	test/raised_called == True

def test_interject(test):
	"""
	# Validate that interject manages to run a callable in a reasonable number of cycles.
	"""
	executed = False
	def call():
		nonlocal executed
		executed = True

	test/executed == False # sanity

	s = signal.signal(signal.SIGUSR2, signal.SIG_IGN)
	try:
		module.interject(call, replacement=False)
		for x in range(32):
			pass
	finally:
		signal.signal(signal.SIGUSR2, s)

	test/executed == True

def test_Invocation_argument_vector(test):
	"""
	# Check for argument property existence.
	"""
	si = module.Invocation.system()
	test/si.argv == si.args

def test_Invocation_imports(test):
	"""
	# Check for a functioning imports method.
	"""
	si = module.Invocation.system()
	si.environ['_test-environ-4'] = 'AAA'

	os.environ['_test-environ'] = '...'
	os.environ['_test-environ-2'] = ',,,'
	os.environ['_test-environ-3'] = '---'
	os.environ['_test-environ-4'] = 'XXX'

	si.imports(['_test-environ'])
	test/si.environ['_test-environ'] == '...'
	test/KeyError ^ (lambda: si.environ['_test-environ-2'])

	si.imports(['_test-environ-2', '_test-environ-3', '_test-environ-4'])
	test/si.environ['_test-environ-2'] == ',,,'
	test/si.environ['_test-environ-3'] == '---'

	test/si.environ['_test-environ-4'] == 'AAA' # local override inhibits import

def test_fs_pwd_no_environ(test):
	"""
	# - &.module.fs_pwd

	# Path instantiation should be successful in the case that PWD is not present.
	"""
	env = os.environ.pop('PWD')
	first = module.fs_pwd()
	test.isinstance(first, module.files.Path)

	os.environ['PWD'] = ''
	second = module.fs_pwd()
	test.isinstance(second, module.files.Path)

	test/first == second

def test_fs_pwd_environ_priority(test):
	"""
	# - &.module.fs_pwd

	# Environment variable is given priority over os.getcwd.
	"""
	os.environ['PWD'] = '/dev/null'
	pwd = module.fs_pwd()
	test/str(pwd) == '/dev/null'

def test_fs_chdir(test):
	"""
	# - &.module.fs_chdir

	# Validate fs_chdir's side effects.
	"""
	pwd = module.fs_chdir('/')
	test/os.environ['PWD'] == '/'
	test/os.getcwd() == '/'
	test.isinstance(pwd, module.files.Path)

	# Validate consistent identity.
	test/id(module.fs_chdir(module.files.root)) == id(module.files.root)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
