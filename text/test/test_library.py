import sys
from .. import library
from .. import core

def test_Parser_emphasis(test):
	function = core.Parser.emphasis
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

if __name__ == '__main__':
	import sys
	from ...development import libtest
	libtest.execute(sys.modules['__main__'])
