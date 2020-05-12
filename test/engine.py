"""
# Harness implementation and support functions.
"""
from . import core

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
		{k : core.Test(v, k) for k, v in container.items()}

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

class Harness(object):
	"""
	# Manage the collection and execution of a set of tests.

	# This is a Test Engine base class that finds and dispatches tests
	# in a hierarchical pattern. Most test runners should subclass
	# &Harness in order to control dispatch and status reporting.
	"""

	Test = core.Test

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

		raise self.Test.Fate(module, subtype='divide')

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

		raise self.Test.Fate(module, subtype='divide')

	def test_root(self, package):
		"""
		# Test subject for loading the root test package within a project.
		"""

		path = str(package)
		project = self.load_test_container(path)

		module = type(core)("test.root")
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
		test = core.Test(id, func)
		with test.exits:
			test.seal()
		if test.fate.impact < 0:
			raise test.fate
