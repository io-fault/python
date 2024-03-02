"""
# Check utility functions present in &.__init__.
"""
from ...route import rewrite as module

def test_rewrite_relative(test):
	"""
	# Check relative path resolution.
	"""
	Function = module.relative
	test/Function(('first', '.', 'second')) == ['first', 'second']
	test/Function(('first', 'second', '..')) == ['first']
	test/Function(('first', 'second', '..', '..')) == []
	test/Function(('first', 'second', '..', '..', '..')) == []
