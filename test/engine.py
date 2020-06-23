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

def test_order(module, name):
	"""
	# Key function used by &gather that uses &get_test_index in
	# order to elevate a test's position given that it was explicitly listed.
	"""
	return get_test_index(getattr(module, name))

def gather(container, prefix='test_', key=test_order, getattr=getattr):
	"""
	# Returns an ordered list of attribute names that match the &prefix.
	"""

	tests = [name for name in dir(container) if name.startswith(prefix)]
	tests.sort() # Order by name first.
	tests.sort(key=(lambda x: key(container, x))) # Re-sort using syntactic positioning.
	return tests

def select(tests, start, stop):
	"""
	# Slice the tests by comparing their identity to &start and &stop.
	"""
	t = None
	i = iter(tests)

	if start is not None:
		for t in i:
			# Skip until start.
			if t == start:
				break
		else:
			return

		# Start of slice.
		yield t

	if stop is None:
		yield from i
	else:
		for t in i:
			yield t
			if t == stop:
				# Skip after stop.
				break

class Harness(object):
	"""
	# Execute a sequence of tests.
	"""

	Test = core.Test
	collect = staticmethod(gather)

	@classmethod
	def from_module(Class, module, identity=None, slices=[]):
		test_ids = Class.collect(module)
		for start, stop in slices:
			test_ids = select(test_ids, start, stop)

		tests = [Class.Test(name, getattr(module, name)) for name in test_ids]
		return Class(identity or module.__name__, module, tests)

	def __init__(self, identity, module, tests):
		"""
		# Create a harness for running the tests in the &package.
		"""
		self.identity = identity
		self.module = module
		self.tests = tests

	def dispatch(self, test):
		"""
		# Dispatch the given &Test to resolve its fate.
		# Subclasses controlling execution will often override this method.
		"""
		with test.exits:
			test.seal()

	def reveal(self):
		"""
		# Reveal the fate of the given tests.
		"""
		for test in self.tests:
			self.dispatch(test)

def execute(module):
	"""
	# Resolve the fate of the tests contained in &module. No status information
	# is printed and the exception of the first failure will be raised.
	"""

	for id in gather(module):
		func = getattr(module, id)
		test = core.Test(id, func)
		with test.exits:
			test.seal()
		if test.fate.impact < 0:
			raise test.fate
