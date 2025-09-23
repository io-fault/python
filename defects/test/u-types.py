import functools
from ...test import types as module

def test_Test_fail(test):
	def test_function(local):
		local.fail("explicit-fail")

	t = module.Test(None, test_function)
	try:
		test_function(t)
	except module.Conclude as err:
		e = err

	test.isinstance(e, module.Conclude)
	test/e.message == "explicit-fail"
	test/e.conclusion == module.TestConclusion.failed
	test/e.failure == module.FailureType.explicit

def test_Test_skip(test):
	def test_function(local):
		local.skip("explicit-skip")

	t = module.Test(None, test_function)
	try:
		test_function(t)
	except module.Conclude as err:
		e = err

	test.isinstance(e, module.Conclude)
	test/e.conclusion == module.TestConclusion.skipped
	test/e.failure == module.FailureType.none

def test_Test_absurdity(test):
	def test_function(local):
		local/1 == 0

	t = module.Test(None, test_function)
	try:
		test_function(t)
	except module.Absurdity as err:
		e = err

	test.isinstance(e, module.Absurdity)

def test_Contention_protocol(test):
	t = module.Test(None, None)
	# protocol
	class O:
		pass
	i = O()
	test.isinstance((t/i), module.Contention)
	test/(t/i)._operand % i

def test_Contention_absurdity(test, partial=functools.partial):
	t = module.Test(None, None)
	test/module.Absurdity ^ partial((t / 1).__ne__, 1)
	test/module.Absurdity ^ partial((t / 1).__eq__, 2)
	test/module.Absurdity ^ partial((t / 2).__lt__, 1)
	test/module.Absurdity ^ partial((t / 1).__gt__, 2)
	test/module.Absurdity ^ partial((t / 1).__ge__, 2)
	test/module.Absurdity ^ partial((t / 3).__le__, 2)
	test/module.Absurdity ^ partial((t / []).__contains__, 2)
	test/module.Absurdity ^ partial((t / []).__lshift__, 2)

	test/module.Absurdity ^ partial(t.isinstance, 2, str)
	test/module.Absurdity ^ partial(t.issubclass, int, str)

	# Check that absurdity is raised when no exception is raised
	test/module.Absurdity ^ partial((t / Exception).__xor__, (lambda: None))

	class LError(Exception):
		def __init__(self, x):
			self.data = x

	def raise_LError():
		raise LError(1)

	# Test contended trap returns the exception.
	x = (t/Exception ^ raise_LError)
	test.isinstance(x, LError)
	test/x.data == 1

def test_Contention_invert_absurdity(test, partial=functools.partial):
	t = module.Test(None, None)
	test/module.Absurdity ^ partial((t.invert/1).__ne__, 0)
	test/module.Absurdity ^ partial((t.invert/1).__eq__, 1)
	test/module.Absurdity ^ partial((t.invert/1).__lt__, 2)
	test/module.Absurdity ^ partial((t.invert/2).__gt__, 1)
	test/module.Absurdity ^ partial((t.invert/2).__ge__, 1)
	test/module.Absurdity ^ partial((t.invert/2).__le__, 3)
	test/module.Absurdity ^ partial((t.invert/[2]).__contains__, 2)
	test/module.Absurdity ^ partial((t.invert/[2]).__lshift__, 2)

	test/module.Absurdity ^ partial(t.invert.isinstance, 2, int)
	test/module.Absurdity ^ partial(t.invert.issubclass, str, str)

	def nothing_raised():
		pass

	x = (t.invert/Exception ^ nothing_raised)

def test_Contention_contextmanager(test):
	t = module.Test(None, None)

	class LError(Exception):
		pass

	# Absurdity not raised from unexpected exception case.
	try:
		with t/ValueError as r:
			raise LError(None)
	except module.Absurdity as exc:
		test.isinstance(exc.__context__, LError)
		test.isinstance(r(), LError)
	except:
		test.fail("absurdity was not raised by contention")
	else:
		test.fail("absurdity was not raised by contention")

	# Expected exception not trapped.
	try:
		with t/ValueError as r:
			raise ValueError("foo")
	except:
		test.fail("exception raised when none was expected")
	else:
		test.isinstance(r(), ValueError)

	# ValueError expected, but no exception raised case.
	try:
		with t/ValueError as r:
			pass
	except module.Absurdity as exc:
		# None meaning no exception trapped at all.
		test/r() == None
	except:
		test.fail("Fail exception was expected")
	else:
		test.fail("Absurdity not raised")

def test_Contention_comparisons(test):
	t = module.Test(None, None)
	t/1 != 2
	t/1 == 1
	t/1 >= 1
	t/1 >= 0
	t/1 <= 2
	t/1 <= 1
	t/1 > 0
	t/0 < 1

	# reverse
	1 != 2/t
	1 == 1/t
	1 >= 1/t
	1 >= 0/t
	1 <= 2/t
	1 <= 1/t
	1 > 0/t
	0 < 1/t

	# perverse
	1/t != 2
	1/t == 1
	1/t >= 1
	1/t >= 0
	1/t <= 2
	1/t <= 1

def test_Contention_containment(test):
	t = module.Test(None, None)
	1 in (t/[1])
	0 in (t.invert/[1])
	t/[1] << 1

	try:
		t/[0] << 1
	except module.Absurdity:
		pass
	else:
		test.fail("absurdity not raised by __lshift__ contention")

def test_Controls_issubclass(test):
	class A(object):
		pass

	class B(A):
		pass

	class C(A):
		pass

	t = module.Test(None, None)
	test/t.issubclass(A, object) == None
	test/t.issubclass(B, A) == None
	test/t.issubclass(C, A) == None
	test/module.Absurdity ^ (lambda: t.issubclass(C, B))

def test_Controls_isinstance(test):
	class A(object):
		pass

	class B(A):
		pass

	class C(A):
		pass

	t = module.Test(None, None)

	test/t.isinstance(A(), object) == None
	test/t.isinstance(B(), A) == None
	test/t.isinstance(C(), A) == None
	test/t.isinstance(C(), C) == None
	test/module.Absurdity ^ (lambda: t.isinstance(C(), B))

def test_itertimer_values(test):
	"""
	# - &module.Test.itertimer
	"""

	t = module.Test(None, None)
	iv = list(t.itertimer(count=100))
	test/iv == list(range(1, len(iv)+1))

def test_itertimer_count_limit(test):
	"""
	# - &module.Test.itertimer
	"""

	t = module.Test(None, None)
	for i in t.itertimer(count=10):
		pass
	test/t.metrics['iterations'] == 10

def test_itertimer_time_limit(test):
	"""
	# - &module.Test.itertimer
	"""

	t = module.Test(None, None)
	for i in t.itertimer(time=0):
		pass
	test/t.metrics['iterations'] == 0

def test_function_timer(test):
	"""
	# - &module.Test.time

	# Validate function timer variant.
	"""

	count = 0
	def invoke():
		nonlocal count
		count += 1

	t = module.Test(None, None)
	t.time(invoke, time=0)
	test/t.metrics.get('iterations', 0) == 0
	t.time(invoke, count=10)
	test/t.metrics['iterations'] == 10

def test_itertimer_Clock(test):
	"""
	# - &module.Test.itertimer

	# Validate clock influence.
	"""

	ns = 1000000000
	time_index = ()

	class LTest(module.Test):
		@staticmethod
		def Clock():
			nonlocal time_index
			for x in time_index:
				return x
			raise Exception("end of time")
	t = LTest(None, None)

	# Check clock first.
	time_index = iter((0, 4 * ns,))
	test/(t.Clock(), t.Clock()) == (0, 4 * ns)

	time_index = iter((0, 4 * ns,))
	for x in t.itertimer():
		pass
	test/t.metrics['iterations'] == 1
	test/t.metrics['timer'] == 4 * ns

	t.metrics['iterations'] = 0
	t.metrics['timer'] = 0
	# Clock is read twice per cycle, so construct pairs of values.
	time_index = iter(map(ns.__mul__, [0, 1, 1, 2, 2, 3, 3, 4]))
	for x in t.itertimer():
		pass
	# Four cycles. scale == 2
	test/t.metrics['iterations'] == (1 + 2 + 4 + 8)
	test/t.metrics['timer'] == 4 * ns

	# Check the rate based constraint where the loop count is reduced
	# by the expected loop time.
	t.metrics['iterations'] = 0
	t.metrics['timer'] = 0
	time_index = iter(map(ns.__mul__, [0, 1, 1, 2, 2, 3, 3, 4]))
	for x in t.itertimer(count=2, time=2):
		pass
	test/t.metrics['iterations'] == 2
	test/t.metrics['timer'] == 2 * ns
	test/LTest.Clock() == 2 * ns
	test/LTest.Clock() == 3 * ns

if __name__ == '__main__':
	import sys
	from .. import engine
	engine.execute(sys.modules['__main__'])
