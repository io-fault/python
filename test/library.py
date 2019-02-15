"""
# Test framework primitives. Provides and defines &Test, &Contention, &Absurdity, and &Fate.
"""
import builtins
import gc
import operator
import functools
import contextlib

def get_test_index(tester, int=int, set=set, AttributeError=AttributeError):
	"""
	# Returns the first line number of the underlying code object.
	"""

	try:
		return int(tester.__test_order__)
	except AttributeError:
		pass

	# no explicit order index
	if '__wrapped__' in tester.__dict__:
		# Resolve the innermost function.
		visited = set((tester,))
		tester = tester.__wrapped__
		while '__wrapped__' in tester.__dict__:
			visited.add(tester)
			tester = tester.__wrapped__
			if tester in visited:
				# XXX: recursive wrappers? warn?
				return None

	try:
		return int(tester.__code__.co_firstlineno)
	except AttributeError:
		return None

def test_order(kv):
	"""
	# Key function used by &gather that uses &get_test_index in
	# order to elevate a test's position given that it was explicitly listed.
	"""
	return get_test_index(kv[1])

def gather(container, prefix = 'test_', key=test_order, getattr=getattr):
	"""
	# Returns an ordered dictionary of attribute names associated with a &Test instance:

	#!/pl/python
		{k : Test(v, k) for k, v in container.items()}

	# Collect the objects in the container whose name starts with "test_".
	# The ordering is defined by the &test_order function.
	"""

	tests = [
		('#'.join((container.__name__, name)), getattr(container, name))
		for name in dir(container)
		if name.startswith(prefix)
	]
	tests.sort(key=key)

	return tests

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

	#!/pl/python
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

		#!/pl/python
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

		#!/pl/python
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

	def __init__(self, content):
		self.content = content

	@property
	def descriptor(self):
		return self.test_fate_descriptors[self.identifier]

	@property
	def negative(self):
		"""
		# Whether the fate's effect should be considered undesirable.
		"""
		return self.impact < 0

	@property
	def contention(self):
		pass

class Pass(Fate):
	abstract = "The test was explicitly passed by a raise."
	impact = 1
	name = "pass"
	code = 0
	color = "green"

class Return(Pass):
	abstract = "The test returned &None implying success."
	impact = 1
	name = "return"
	code = 1
	color = "green"

class Explicit(Pass):
	abstract = "The test must be explicitly invoked."
	impact = 0
	name = "explicit"
	code = 2
	color = "magenta"

class Skip(Pass):
	abstract = "The test was skipped for a specific reason."
	impact = 0
	name = "skip"
	code = 3
	color = "cyan"

class Divide(Fate):
	abstract = "The test is a container of a set of tests."
	impact = 1 # This is positive as the division may have performed critical imports.
	name = "divide"
	code = 4
	color = "blue"

	def __init__(self, container, limit = 1):
		self.content = container
		self.tests = []
		self.limit = limit

class Fail(Fate):
	abstract = "The test raised an exception or contended an absurdity."
	impact = -1
	name = "fail"
	code = 5
	color = "red"

class Void(Fail):
	abstract = "The coverage data of the test does not meet expectations."
	name = "void"
	code = 6
	color = "red"

class Expire(Fail):
	abstract = "The test did not finish in the configured time."
	name = "expire"
	code = 8
	color = "yellow"

class Interrupt(Fail):
	abstract = "The test was interrupted by a control exception."
	name = "interrupt"
	code = 9
	color = "orange"

class Core(Fail):
	"""
	# Failure cause by a process dropping a core image or similar uncontrollable crash.

	# This exception is used by advanced test harnesses that execute tests in subprocesses to
	# protect subsequent tests.
	"""

	abstract = 'The test caused a core image to be produced by the operating system.'
	name = 'core'
	code = 90
	color = 'orange'

fate_exceptions = {
	x.name: x
	for x in [
		Fate,
		Pass,
		Return,
		Explicit,
		Skip,
		Divide,
		Fail,
		Void,
		Expire,
		Interrupt,
		Core,
	]
}

class Test(object):
	"""
	# An object that manages an individual test and its execution.
	# Provides interfaces for constructing and checking &Contention's using
	# a simple syntax.

	# [ Properties ]

	# /identity/
		# A unique identifier for the &Test. Usually, a qualified name that can be used to
		# locate &subject without having the actual object.

	# /subject/
		# The callable that performs a series of checks--using the &Test instance--that
		# determines the &fate.

	# /fate/
		# The conclusion of the Test; pass, fail, error, skip. An instance of &Fate.

	# /exits/
		# A &contextlib.ExitStack for cleaning up allocations made during the test.
		# The harness running the test decides when the stack's exit is processed.
	"""
	__slots__ = ('subject', 'identity', 'constraints', 'fate', 'exits',)

	# These referenced via Test instances to allow subclasses to override
	# the implementations.
	Absurdity = Absurdity
	Contention = Contention

	Fate = Fate

	Pass = Pass
	Return = Return

	Explicit = Explicit
	Skip = Skip
	Divide = Divide

	Fail = Fail
	Void = Void
	Expire = Expire

	# criticals
	Interrupt = Interrupt
	Core = Core

	def __init__(self, identity, subject, *constraints, ExitStack=contextlib.ExitStack):
		# allow explicit identity as the callable may be a wrapped function
		self.identity = identity
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
			self.fail("test has already been sealed") # recursion protection

		self.fate = None

		try:
			r = self.subject(self)
			# Make an attempt at causing any deletions.
			gc.collect()
			if not isinstance(r, self.Fate):
				self.fate = self.Return(r)
			else:
				self.fate = r
		except (self.Pass, self.Divide) as exc:
			tb = exc.__traceback__ = exc.__traceback__.tb_next
			self.fate = exc
		except BaseException as err:
			# libtest traps any exception raised by a particular test.

			if not isinstance(err, Exception) and not isinstance(err, Fate):
				# a "control" exception.
				# explicitly note as interrupt to consolidate identification
				self.fate = self.Interrupt('test raised interrupt')
				self.fate.__cause__ = err
				raise err # e.g. kb interrupt
			elif not isinstance(err, Fate):
				# regular exception; a failure
				tb = err.__traceback__ = err.__traceback__.tb_next
				self.fate = self.Fail('test raised exception')
				self.fate.__cause__ = err
			else:
				tb = err.__traceback__ = err.__traceback__.tb_next
				self.fate = err

		if tb is not None:
			self.fate.line = tb.tb_lineno

	def explicit(self):
		"""
		# Used by test subjects to inhibit runs of a particular test in aggregate runs.
		"""
		raise self.Explicit("test must be explicitly invoked in order to run")

	def skip(self, condition):
		"""
		# Used by test subjects to skip the test given that the provided &condition is
		# &True.
		"""
		if condition: raise self.Skip(condition)

	def fail(self, cause):
		raise self.Fail(cause)

	def timeout(self, *args, cause='signal'):
		raise self.Expire(cause)

	def trap(self):
		"""
		# Set a trap for exceptions converting a would-be &Error fate on exit to a &Failure.

		#!/pl/python
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
				raise test.Fail('missed garbage collection expectation')
		del collect
	except ImportError:
		def garbage(self, *args, **kw):
			"""
			# Garbage collection not available.
			"""
			pass

class Harness(object):
	"""
	# Manage the collection and execution of a set of tests.

	# This is a Test Engine base class that finds and dispatches tests
	# in a hierarchical pattern. Most test runners should subclass
	# &Harness in order to control dispatch and status reporting.
	"""

	Test = Test
	Fail = Fail
	Divide = Divide
	Core = Core

	def __init__(self, package):
		"""
		# Create a harness for running the tests in the &package.
		"""
		self.package = package

	@staticmethod
	def collect_subjects(container):
		"""
		# Prepare a collection of test subjects with their corresponding identifier
		# for subsequent execution.
		"""
		return gather(container)

	@staticmethod
	def load_test_container(identifier):
		"""
		# Load a set of tests that can be addressed using the given &identifier.

		# Default implementation uses &importlib.import_module.
		"""
		from importlib import import_module
		return import_module(str(identifier))

	@staticmethod
	def listpkg(path):
		"""
		# List the modules contained by the given path.
		"""

		from pkgutil import iter_modules
		for (importer, name, ispkg) in iter_modules(path) if path is not None else ():
			yield (ispkg, name)

	def test_module(self, test):
		"""
		# Test subject for loading modules and dividing their contained tests.
		"""

		module = self.load_test_container(test.identity)
		test/module.__name__ == test.identity

		module.__tests__ = self.collect_subjects(module)
		if '__test__' in dir(module):
			# allow module to skip the entire set
			module.__test__(test)

		raise self.Divide(module)

	def test_package(self, test):
		"""
		# Test subject for loading packages and dividing their contained modules.
		"""

		module = self.load_test_container(test.identity)
		test/module.__name__ == test.identity
		name = module.__name__

		if 'context' in dir(module):
			module.context(self)

		seq = list(self.listpkg(module.__path__))
		module.__tests__ = [
			('.'.join((name, x[1])), self.test_module)
			for x in seq
			if not x[0] and x[1][:5] == 'test_'
		]
		module.__tests__.extend([
			('.'.join((name, x[1])), self.test_package)
			for x in seq if x[0]
		])

		raise self.Divide(module)

	def test_root(self, package):
		"""
		# Test subject for loading the root test package within a project.
		"""

		path = str(package)
		project = self.load_test_container(path)

		module = type(builtins)("test.root")
		module.__tests__ = [(path + '.test', self.test_package)]

		return module

	def dispatch(self, test):
		"""
		# Dispatch the given &Test to resolve its fate.
		# Subclasses controlling execution will often override this method.
		"""

		with test.exits:
			test.seal()

	def process(self, container, modules):
		"""
		# Dispatch the set of test subjects declared within the container's `__tests__` attribute.

		# The tests attribute should be a sequence of identifier-subject pairs that can be
		# used construct a &Test instance.
		"""

		for tid, tcall in getattr(container, '__tests__', ()):
			test = self.Test(tid, tcall)
			self.dispatch(test)

def execute(module):
	"""
	# Resolve the fate of the tests contained in &module. No status information
	# is printed and the exception of the first failure will be raised.
	"""

	for id, func in gather(module):
		test = Test(id, func)
		with test.exits:
			test.seal()
		if test.fate.impact < 0:
			raise test.fate
