import sys
from ...status import python
from ...status import types

def stack_1(error=None):
	if error is None:
		return list(python.iterstack(sys._getframe())) # 1
	else:
		raise error # 1 not none

def stack_2(error):
	return stack_1(error) or 1 # 2

def stack_3(error):
	return stack_2(error) or 2 # 3

def stack_4(error):
	return stack_3(error) or 3 # 4

def stack_5(error):
	return stack_4(error) or 4 # 5

def test_iterstack(test):
	"""
	# - &python.iterstack

	# Additionally checks coherency of the Python runtime.
	"""

	one_level = stack_1(None)
	rlength = len(one_level)

	test/rlength > 1

	five_levels = stack_5(None)
	test/len(five_levels) == (rlength + 4)

def test_itertraceback(test):
	"""
	# - &python.itertraceback

	# Additionally checks coherency of the Python runtime.
	"""

	one_level = stack_1(None)
	error = Exception("raise branch")
	try:
		stack_1(error)
	except Exception as raised:
		one_level = list(python.itertraceback(raised.__traceback__))

	rlength = len(one_level)

	test/rlength == 2

	error = Exception("raise branch")
	try:
		stack_5(error)
	except Exception as raised:
		five_levels = list(python.itertraceback(raised.__traceback__))

	test/len(five_levels) == (rlength + 4)
