from ...context import types as module

def test_Cell_iteration(test):
	"""
	# - &module.Cell.__iter__
	"""
	values = [0, 1, "text"]
	for v in values:
		c = module.Cell(v)
		for x in c:
			test/x == v

def test_Cell_coalesce(test):
	"""
	# - &module.Cell.coalesce
	"""
	nothing = module.Cell(None)
	test/nothing.coalesce(1) == 1
	test/nothing.coalesce(None) == None

	something = module.Cell("text")
	test/something.coalesce(1) == "text"
	test/something.coalesce(None) == "text"

def test_Cell_sequence(test):
	values = [0, 1, "text"]
	for v in values:
		c = module.Cell(v)
		test/c.element == v
		test/c[0] == v
		test/list(c) == [v]

		test/(v in c) == True
		test/(None in c) == False

		test/ValueError ^ (lambda: c.index(None))
		test/ValueError ^ (lambda: c.index(v, start=1))
		test/ValueError ^ (lambda: c.index(v, stop=0))
		test/reversed(c) == c
		test/c.index(v) == 0
		test/c.count(v) == 1
		test/c.count(None) == 0

def test_Cell_equality(test):
	"""
	# - &module.Cell.__eq__
	"""
	values = [0, 1, "text"]
	for v in values:
		c = module.Cell(v)
		test/c.element == v
		test/c[0] == v
		test/list(c) == [v]
		test/reversed(c) == c

def test_Cell_setup(test):
	"""
	# - &module.Cell.__setup__
	"""
	import collections.abc
	module.Cell.__setup__()
	c = module.Cell(None)
	test.isinstance(c, collections.abc.Sequence)
	test.isinstance(c, collections.abc.Iterable)
