"""
# Test framework primitives. Provides and defines &Test, &Contention, &Absurdity, and &Fate.
"""
import builtins
import gc
import operator
import functools
import contextlib

class Absurdity(Exception):
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
	}

	def __init__(self, operator, former, latter, inverse=None):
		self.operator = operator
		self.former = former
		self.latter = latter
		self.inverse = inverse

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
			test/featurelib.functionality() == expectation

	# True division, "/", is used as it has high operator precedance that allows assertion
	# expresssions to be constructed using minimal syntax that lends to readable failure
	# conditions.

	# All of the comparison operations are supported by Contention and are passed on to the
	# underlying objects being examined.
	"""
	__slots__ = ('test', 'object', 'storage', 'inverse')

	def __init__(self, test, object, inverse=False):
		self.test = test
		self.object = object
		self.inverse = inverse

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

			def check(self, ob, opname = opname, operator = v):
				test, x, y = self.test, self.object, ob
				if self.inverse:
					if operator(x, y): raise self.test.Absurdity(opname, x, y, inverse=True)
				else:
					if not operator(x, y): raise self.test.Absurdity(opname, x, y, inverse=False)
			locals()[k] = check

	##
	# Special cases for context manager exception traps.

	def __enter__(self, partial = functools.partial):
		return partial(getattr, self, 'storage', None)

	def __exit__(self, typ, val, tb):
		test, x = self.test, self.object
		y = self.storage = val
		if isinstance(y, test.Fate):
			# Don't trap test Fates.
			# The failure has already been analyzed or some
			# other effect is desired.
			return

		if not isinstance(y, x): raise self.test.Absurdity("isinstance", x, y)
		return True # !!! Inhibiting raise.

	def __xor__(self, subject):
		"""
		# Contend that the &subject raises the given exception when it is called::

		#!syntax/python
			test/Exception ^ (lambda: subject())

		# Reads: "Test that 'Exception' is raised by 'subject'".
		"""
		with self as exc:
			subject()
		return exc()
	__rxor__ = __xor__

	def __lshift__(self, subject):
		"""
		# Contend that the parameter is contained by the object, &Container::

		#!syntax/python
			test/Container << subject

		# Reads: "Test that 'Container' contains 'subject'".
		"""
		return subject in self.object
	__rlshift__ = __lshift__

class Fate(BaseException):
	"""
	# The Fate of a test. &Test.seal uses &Fate exceptions to describe the result of a unit test.
	"""
	name = 'fate'
	content = None
	impact = None
	line = None
	color = 'white'

	test_fate_descriptors = {
		# Abstract, Impact, Numeric Identifier, Color
		'return': ("passed", "The test returned without exception implying success",1,0,"green"),
		'pass': ("passed", "The test was explicitly passed by raising its Fate",1,1,"green"),
		'explicit': ("skipped", "The test must be explicitly invoked",0,2,"magenta"),
		'skip': ("skipped", "The test was skipped for a specific reason",0,3,"cyan"),
		'divide': ("divided", "The test is a container of a set of tests",1,4,"blue"),
		'fail': ("failed", "The test raised an exception or contended an absurdity",-1,5,"red"),
		'absurdity': ("failed", "The test contended an absurdity",-1,5,"red"),
		'exception': ("failed", "The test's execution resulted in an exception",-1,5,"red"),
		'reveal': ("revealed", "The coverage data of the test does not meet expectations",-1,6,"red"),
		'expire': ("expired", "The test did not finish in the configured time",-1,8,"yellow"),
		'interrupt': ("interrupted", "The test was interrupted by a control exception",-1,9,"orange"),
		'core': ("cored", "The test caused a core image to be produced by the operating system",-1,90,"orange"),
	}

	def __init__(self, content, subtype=None):
		self.content = content
		self.subtype = subtype or self.name

	@property
	def descriptor(self):
		return self.test_fate_descriptors[self.subtype]

	@property
	def impact(self):
		return self.descriptor[2]

	@property
	def negative(self):
		"""
		# Whether the fate's effect should be considered undesirable.
		"""
		return self.impact < 0

	@property
	def contention(self):
		pass

class Test(object):
	"""
	# An object that manages an individual test and its execution.
	# Provides interfaces for constructing and checking &Contention's using
	# a simple syntax.

	# [ Properties ]

	# /identifier/
		# The key used to retrieve the test function from the container.

	# /subject/
		# The callable that performs a series of checks--using the &Test instance--that
		# determines the &fate.

	# /fate/
		# The conclusion of the Test; pass, fail, error, skip. An instance of &Fate.

	# /exits/
		# A &contextlib.ExitStack for cleaning up allocations made during the test.
		# The harness running the test decides when the stack's exit is processed.
	"""
	__slots__ = ('subject', 'identifier', 'constraints', 'fate', 'exits',)

	# These referenced via Test instances to allow subclasses to override
	# the implementations.
	Absurdity = Absurdity
	Contention = Contention
	Fate = Fate

	def __init__(self, identifier, subject, *constraints, ExitStack=contextlib.ExitStack):
		# allow explicit identifier as the callable may be a wrapped function
		self.identifier = identifier
		self.subject = subject
		self.constraints = constraints
		self.exits = ExitStack()

	def __truediv__(self, object):
		return self.Contention(self, object)

	def __rtruediv__(self, object):
		return self.Contention(self, object)

	def __floordiv__(self, object):
		return self.Contention(self, object, True)

	def __rfloordiv__(self, object):
		return self.Contention(self, object, True)

	def isinstance(self, *args):
		if not builtins.isinstance(*args):
			raise self.Absurdity("isinstance", *args, inverse=True)

	def issubclass(self, *args):
		if not builtins.issubclass(*args):
			raise self.Absurdity("issubclass", *args, inverse=True)

	def seal(self, isinstance=builtins.isinstance, BaseException=BaseException, Exception=Exception, Fate=Fate):
		"""
		# Seal the fate of the Test by executing the subject-callable with the Test
		# instance as the only parameter.

		# Any exception that occurs is trapped and assigned to the &fate attribute
		# on the Test instance. &None is always returned by &seal.
		"""

		tb = None
		if hasattr(self, 'fate'):
			raise RuntimeError("test has already been sealed")

		self.fate = None

		try:
			r = self.subject(self)
			# Make an attempt at causing any deletions.
			gc.collect()
			if not isinstance(r, self.Fate):
				self.fate = self.Fate(r, subtype='return')
			else:
				self.fate = r
		except BaseException as err:
			if isinstance(err, self.Fate):
				tb = err.__traceback__ = err.__traceback__.tb_next
				self.fate = err
			elif not isinstance(err, Exception):
				# a "control" exception.
				# explicitly note as interrupt to consolidate identification
				self.fate = self.Fate('test raised interrupt', subtype='interrupt')
				self.fate.__cause__ = err
				raise err # e.g. kb interrupt
			else:
				# regular exception; a failure
				tb = err.__traceback__ = err.__traceback__.tb_next
				self.fate = self.Fate('test raised exception', subtype='fail')
				self.fate.__cause__ = err

		if tb is not None:
			self.fate.line = tb.tb_lineno

	def explicit(self):
		"""
		# Used by test subjects to inhibit runs of a particular test in aggregate runs.
		"""
		raise self.Fate("test must be explicitly invoked in order to run", subtype='explicit')

	def skip(self, condition):
		"""
		# Used by test subjects to skip the test given that the provided &condition is
		# &True.
		"""
		if condition: raise self.Fate(condition, subtype='skip')

	def fail(self, cause):
		raise self.Fate(cause, subtype='fail')

	def timeout(self, *args, cause='signal'):
		raise self.Fate(cause, subtype='expire')

	def trap(self):
		"""
		# Set a trap for exceptions converting a would-be &Error fate on exit to a &Failure.

		#!syntax/python
			with test.trap():
				...

		# This allows &fail implementations set a trace prior to exiting
		# the test's &subject.

		# &Fate exceptions are not trapped.
		"""
		return (self / None.__class__)

	# gc collect() interface. no-op if nothing
	try:
		from gc import collect
		def garbage(self, minimum = None, collect = collect, **kw):
			"""
			# Request collection with the expectation of a minimum unreachable.

			# Used by tests needing to analyze the effects garbage collection.
			"""
			unreachable = collect()
			if minimum is not None and (
				unreachable < minimum
			):
				raise test.Fail("missed garbage collection expectation")
		del collect
	except ImportError:
		def garbage(self, *args, **kw):
			"""
			# Garbage collection not available.
			"""
			pass
