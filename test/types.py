"""
# Test framework primitives.
"""
import builtins
import operator
import functools
import contextlib
import enum

try:
	from ..system import clocks
except ImportError:
	try:
		from time import monotonic as _python_time
	except AttributeError:
		try:
			from time import time as _python_time
		except:
			# Issue warning.
			_python_time = (lambda: 0)

	system_time_clock = (lambda: int(_python_time() * 1000000000))
else:
	_python_time = None
	system_time_clock = clocks.Monotonic().get

class FailureType(enum.Enum):
	"""
	# The type of test failure that occurred.

	# [ Elements ]
	# /never/
		# Test was not ran or the conclusion could not be integrated.
	# /limit/
		# Resource limit exceeded.
	# /interrupt/
		# Test was interrupted by administrator.
	# /explicit/
		# Test failure was directly concluded by the function.
	# /none/
		# Test did not fail. The failure of passed or skipped tests.
	# /absurdity/
		# Test contended absurdity.
	# /fault/
		# Fault detected or trapped during testing.
		# Critical process signal(SIGSEGV), language exception,
		# or even promoted application errors.
	"""

	never     = -4
	limit     = -3
	interrupt = -2
	explicit  = -1
	none      =  0
	absurdity = +1
	fault     = +2

	descriptions = (
		"The test did not fail.", # none
		"The test contended an absurdity.",
		"The test could not be completed due to an exception or critical process signal.",
		"The test function never ran or the conclusion could not be recognized.", # -4
		"The test exceeded a harness imposed resource limit.", # -3, limit
		"The test was interrupted by an administrator.", # -2, interrupt
		"The test function directly concluded failure.", # -1, explicit
	)

class TestConclusion(enum.Enum):
	"""
	# The possible results of a test.

	# [ Elements ]
	# /failed/
		# The test did not pass.
		# An associated &Failure should be non-zero describing what happened.
	# /skipped/
		# The test was identified as not being applicable to the execution context.
	# /passed/
		# The test executed without failure.
	"""

	failed  = -1
	skipped =  0
	passed  = +1

	descriptions = (
		"The test was skipped.",
		"The test passed.",
		"The test failed.",
	)

	def not_failure(self):
		return self != self.__class__.failed

class TestControl(Exception):
	def __init__(self, message):
		self.message = message

class Conclude(TestControl):
	"""
	# Control exception for concluding a test.
	"""

	def __init__(self, conclusion, failure, message):
		super().__init__(message)
		self.conclusion = conclusion
		self.failure = failure

class Absurdity(TestControl):
	"""
	# Exception raised by &Contention instances designating a failed assertion.
	"""

	# for re-constituting the expression
	operator_names_mapping = {
		'__eq__': '==',
		'__ne__': '!=',
		'__le__': '<=',
		'__ge__': '>=',

		'__mod__': 'is',
		'__lshift__': '<<',
	}

	def __init__(self, operator, former, latter, inverse=None):
		self.operator = operator
		self.former = former
		self.latter = latter
		self.inverse = inverse
		super().__init__(str(self))

	def __str__(self):
		opchars = self.operator_names_mapping.get(self.operator, self.operator)
		prefix = ('not ' if self.inverse else '')
		return prefix + ' '.join((repr(self.former), opchars, repr(self.latter)))

	def __repr__(self):
		return '{0}({1!r}, {2!r}, {3!r}, inverse={4!r})'.format(
			self.__name__, self.operator, self.former, self.latter, self.inverse
		)

# Exposes an assert like interface to Test objects.
class Contention(object):
	"""
	# Contentions are objects used by &Test objects to provide assertions.
	# Usually, contention instances are made by the true division operator of
	# &Test instances passed into unit test subjects.

	#!syntax/python
		import featurelib

		def test_feature(test):
			expectation = ...
			test/expectation == featurelib.functionality()

	# True division, "/", is used as it has high operator precedance that allows assertion
	# expresssions to be constructed using minimal syntax that lends to readable failure
	# conditions.

	# All of the comparison operations are supported by Contention and are passed on to the
	# operands being examined.
	"""

	__slots__ = ('_operand', '_inverse', '_storage')
	_operand: object
	_inverse: bool
	_storage: object

	def __init__(self, object, inverse=False):
		self._operand = object
		self._inverse = inverse

	# Build operator methods based on operator.
	_override = {
		'__mod__' : ('is', lambda x,y: x is y)
	}

	for k, v in operator.__dict__.items():
		if k.startswith('__get') or k.startswith('__set'):
			continue
		if k.strip('_') in operator.__dict__:
			if k in _override:
				opname, v = _override[k]
			else:
				opname = k

			def check(self, operand:object, opname=opname, operator=v, /, __traceframe__='fault-contention'):
				x = self._operand
				y = operand
				if self._inverse:
					if operator(x, y): raise Absurdity(opname, x, y, inverse=True)
					return False
				else:
					if not operator(x, y): raise Absurdity(opname, x, y, inverse=False)
					return True
			locals()[k] = check

	def __enter__(self, partial=functools.partial):
		return partial(getattr, self, '_storage', None)

	def __exit__(self, typ, val, tb):
		x = self._operand
		y = self._storage = val

		if self._inverse:
			if isinstance(y, x): raise Absurdity("isinstance", x, y, inverse=True)
		else:
			if not isinstance(y, x): raise Absurdity("isinstance", x, y, inverse=False)
		return True # Trap the exception if it is expected.

	def __xor__(self, operand):
		"""
		# Contend that the &operand raises the given exception when it is called.

		#!syntax/python
			test/Exception ^ (lambda: callabel())
		"""

		with self as exc:
			operand() # Exception test.
		return exc()

	def __lshift__(self, operand):
		"""
		# Contend that the &operand is contained by the object.

		#!syntax/python
			test/Container << operand
		"""

		contained = operand in self._operand

		if self._inverse:
			if contained: raise Absurdity("__contains__", self._operand, operand, inverse=True)
			return False
		else:
			if not contained: raise Absurdity("__contains__", self._operand, operand, inverse=False)
			return True

class Test(object):
	"""
	# An object that manages an individual test and its execution.
	# Provides interfaces for constructing and checking &Contention's using
	# a simple syntax.

	# [ Elements ]
	# /function/
		# The callable that performs a series of checks--using the &Test instance--that
		# determines the &fate.
	# /identifier/
		# The key used to retrieve the test function from the container.
	# /exits/
		# A &contextlib.ExitStack for cleaning up allocations made during the test.
		# The harness running the test decides when the stack's exit is processed.
	# /metrics/
		# A set of measurements included in the test's report.
		# Primarily, `'duration'`, `'usage'`, `'contentions'`, `'timer'`, `'iterations'`.
	# /conclusion/
		# The conclusion of the Test; fail, pass, or skip. &None if not concluded.
	# /failure/
		# The failure type of a concluded Test; &FailureType.
	"""

	__slots__ = (
		'function', 'identifier', 'exits',
		'metrics', 'conclusion', 'failure',
		'exception', 'traceback',
		'_invert_contention',
	)

	# These referenced via Test instances to allow subclasses to override
	# the implementations.
	Clock = system_time_clock
	Absurdity = Absurdity
	Contention = Contention

	failure: FailureType
	conclusion: TestConclusion
	_invert_contention: int

	@property
	def line(self):
		return self.traceback.tb_lineno

	def __init__(self, identifier, function, *constraints,
			ExitStack=contextlib.ExitStack, Metrics=dict,
		):
		# allow explicit identifier as the callable may be a wrapped function
		self.identifier = identifier
		self.function = function
		self.conclusion = None
		self.failure = None
		self.exits = ExitStack()
		self.metrics = Metrics()
		self.metrics['duration'] = 0
		self.metrics['contentions'] = 0
		self._invert_contention = 0

	def _inverse(self):
		if self._invert_contention:
			self._invert_contention -= 1
			i = True
		else:
			i = False

		return i

	def _absurd(self, inverse, truth):
		if not truth and not inverse:
			return True
		if inverse and truth:
			return True
		return False

	@property
	def invert(self):
		"""
		# Invert the next contention; absurdity is coherent and coherence is absurd.
		"""

		self._invert_contention += 1
		return self

	def __truediv__(self, operand):
		self.metrics['contentions'] += 1
		return self.Contention(operand, inverse=self._inverse())

	def __rtruediv__(self, operand):
		self.metrics['contentions'] += 1
		return self.Contention(operand, inverse=self._inverse())

	def isinstance(self, *args):
		self.metrics['contentions'] += 1
		i = self._inverse()
		if self._absurd(i, builtins.isinstance(*args)):
			raise Absurdity("isinstance", *args, inverse=i)

	def issubclass(self, *args):
		self.metrics['contentions'] += 1
		i = self._inverse()
		if self._absurd(i, builtins.issubclass(*args)):
			raise self.Absurdity("issubclass", *args, inverse=i)

	def itertimer(self, units=1, /,
			count=5**10, time=4, scale=2, cycle=100000,
			identity=('iterations', 'timer'),
			min=min, range=range, int=int,
		):
		"""
		# Measure the relative performance of a loop's iterations.

		# [ Parameters ]
		# /units/
			# The factor to increase the iteration count by.
			# Used when the for-loop contains repeated statements for
			# improved precision.
		# /count/
			# The maximum number of iterations to perform.
		# /time/
			# The maximum duration of the timer in seconds.
		# /scale/
			# The factor to increase the cycle loop count by.
		# /cycle/
			# The maximum number of iterations to perform within a cycle.
			# Used to limit the effects of the &scale factor.
		"""
		# nanoseconds
		time *= 1000000000

		ti = 0
		ci = 0
		loops = 1

		tell = self.Clock

		try:
			# Run until either time or count limit is reached.
			while ci < count and ti < time:
				iloops = min(loops, count - ci)
				irange = range(ci+1, ci+iloops+1)

				before = tell()
				yield from irange
				after = tell()

				delta = after - before
				ci += (iloops * units)
				ti += delta

				# Progressively perform more iterations, but
				# limit to the cycle maximum.
				loops = int(scale * loops)
				loops = min(loops, cycle)

				# Given the current rate and remaining duration, identify whether or not
				# to reduce the cycle's loop count further.
				remainder = time - ti
				rate = ci / (ti or 1)
				loops = min(loops, int(remainder / rate))
		finally:
			for k, v in zip(identity, (ci, ti)):
				self.metrics[k] = self.metrics.get(k, 0) + v

	def time(self, callable, **kw):
		"""
		# Measure the relative performance of the given callable.
		"""

		for i in self.itertimer(1, **kw):
			callable()

	def skip(self, condition):
		"""
		# Explicitly conclude that the test skipped when &condition is &True.
		"""

		if condition: raise Conclude(TestConclusion.skipped, FailureType.none, "skipped")

	def fail(self, message=None):
		"""
		# Explicitly conclude that the test failed.
		"""

		raise Conclude(TestConclusion.failed, FailureType.explicit, message)

	def _timeout(self, *args):
		raise Conclude(
			TestConclusion.failed,
			FailureType.limit,
			"test exceeded real time duration limit"
		)

	# gc collect() interface. no-op if nothing
	try:
		from gc import collect
		def garbage(self, minimum=None, *, collect=collect):
			"""
			# Request collection with the expectation of a minimum unreachable.

			# Used by tests needing to analyze the effects garbage collection.
			"""

			unreachable = collect()
			if minimum is not None and (
				unreachable < minimum
			):
				raise Conclude(
					TestConclusion.failed,
					FailureType.absurdity,
					"missed garbage collection expectation"
				)
		del collect
	except ImportError:
		def garbage(self, minimum=None):
			"""
			# Garbage collection not available.
			"""
			pass
