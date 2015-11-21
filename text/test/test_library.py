import sys
from .. import library

def test_Parser_emphasis(test):
	function = library.Parser.emphasis
	test/list(function("No emphasis")) == [('text', "No emphasis")]

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1)]
	test/list(function("Some *emphasis!*")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1), ('text', ' and following.')]
	test/list(function("Some *emphasis!* and following.")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 2), ('text', ' and following.')]
	test/list(function("Some **emphasis!** and following.")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 3), ('text', ' and following.')]
	test/list(function("Some ***emphasis!*** and following.")) == expect

	# Pair of emphasized ranges.
	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1),
		('text', ', '), ('emphasis', 'twice', 1), ('text', '!')]
	test/list(function("Some *emphasis!*, *twice*!")) == expect

	# Three emphasized ranges.
	expect = [('text', "Some "),
		('emphasis', 'emphasis!', 1), ('text', ', not '),
		('emphasis', 'twice', 2), ('text', ', but '),
		('emphasis', 'thrice', 1), ('text', '!')]
	test/list(function("Some *emphasis!*, not **twice**, but *thrice*!")) == expect

def test_PythonNamespace(test):
	import builtins
	pn = library.PythonNamespace()
	x = library.__name__
	test/pn.select(x) == (x, None, [(x, library)])

	test/pn.select(x + '.Context') == (x, 'Context', [(x, library), ('Context', library.Context)])
	test/pn.select(x + '.Context.__init__') == (x, 'Context.__init__', [
		(x, library),
		('Context', library.Context),
		('__init__', library.Context.__init__),
	])

	# builtins reference
	test/pn.select('str') == ('builtins', 'str', [('builtins', builtins), ('str', str)])
	test/pn.select('int') == ('builtins', 'int', [('builtins', builtins), ('int', int)])

	# standard library module
	import collections
	test/pn.select('collections.deque') == ('collections', 'deque', [
		('collections', collections), ('deque', collections.deque)
	])

def test_PythonRelativeNamespace(test):
	# usually a per-project namespace
	pn = library.PythonRelativeNamespace(library.__package__)
	test/pn.select('.libeclectic.Context') == pn.select(library.__name__ + '.Context')

if __name__ == '__main__':
	import sys
	from ...development import libtest
	libtest.execute(sys.modules['__main__'])
