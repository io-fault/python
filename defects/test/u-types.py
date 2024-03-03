import functools
from ...test import types as module

def test_Test_fail(test):
	def test_function(local):
		local.fail("foo")
	t = module.Test(None, test_function)
	t.seal()
	test.isinstance(t.fate, module.Fate)
	test/t.fate.subtype == 'fail'
	test/"foo" == t.fate.content

def test_Test_error(test):
	def t(test):
		raise TypeError("foo")
	t = module.Test(None, t)
	t.seal()
	test.isinstance(t.fate, module.Fate)
	test/t.fate.subtype == 'fail'

def raise_parameter(excvalue):
	raise excvalue

def test_Test_skip(test):
	def f(it):
		it.skip("test")
	t = module.Test(None, f)
	t.seal()
	test.isinstance(t.fate, module.Fate)
	test/t.fate.subtype == 'skip'
	test/"test" == t.fate.content

def test_Contention(test, partial = functools.partial):
	t = module.Test(None, None)
	# protocol
	test.isinstance((t/1), module.Contention)
	test/(t/1).test == t
	test/(t/1).object == 1

	test/module.Absurdity ^ partial((t / 1).__ne__, 1)
	test/module.Absurdity ^ partial((t / 1).__eq__, 2)
	test/module.Absurdity ^ partial((t / 2).__lt__, 1)
	test/module.Absurdity ^ partial((t / 1).__gt__, 2)
	test/module.Absurdity ^ partial((t / 1).__ge__, 2)
	test/module.Absurdity ^ partial((t / 3).__le__, 2)
	test/module.Absurdity ^ partial((t / []).__contains__, 2)

	test/module.Absurdity ^ partial(t.isinstance, 2, str)
	test/module.Absurdity ^ partial(t.issubclass, int, str)

	try:
		with t/ValueError as r:
			raise OSError("foo")
	except module.Absurdity as exc:
		test.isinstance(exc.__context__, OSError)
		test.isinstance(r(), OSError)
	else:
		test.fail("subject did not catch unexpected")

	try:
		with t/ValueError as r:
			raise ValueError("foo")
		test.isinstance(r(), ValueError)
	except:
		test.fail("exception raised when none was expected")

	try:
		with t/ValueError as r:
			pass
		test.fail("did not raise")
	except module.Absurdity as exc:
		test/r() == None
		pass # passed
	except:
		test.fail("Fail exception was expected")

	class Foo(Exception):
		def __init__(self, x):
			self.data = x

	def raise_Foo():
		raise Foo(1)

	x = t/Exception ^ raise_Foo
	# return was the trapped exception
	t/x.data == 1
	test/module.Absurdity ^ partial((t / Exception).__xor__, (lambda: None))

	# any exceptions are failures
	t/1 != 2
	t/1 == 1
	t/1 >= 1
	t/1 >= 0
	t/1 <= 2
	t/1 <= 1
	1 in (t/[1])
	0 in (t//[1])

	# reverse
	1 != 2/t
	1 == 1/t
	1 >= 1/t
	1 >= 0/t
	1 <= 2/t
	1 <= 1/t

	# perverse
	1/t != 2
	1/t == 1
	1/t >= 1
	1/t >= 0
	1/t <= 2
	1/t <= 1

	class A(object):
		pass
	class B(A):
		pass

	t.issubclass(B, A)
	t.isinstance(B(), B)
	t.isinstance(B(), A)

def test_issubclass(test):
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

def test_isinstance(test):
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
