import sys
from .. import python
from .. import types

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

def test_traceframes(test):
	"""
	# - &python.traceframes
	"""

	error = None
	try:
		stack_5(1)
	except Exception as e:
		error = e
		trace = python.traceframes(python.itertraceback(e.__traceback__))

	test.isinstance(trace, types.Trace)
	test.isinstance(trace.t_route[0][0], types.EStruct)
	test.isinstance(trace.t_route[0][1], types.Parameters)

	i = 0
	for event, params in reversed(trace.t_route):
		i += 1
		if i >= 6:
			break

		ss = "# " + str(i)
		sym = 'stack_' + str(i)

		test/event.abstract.find(ss) != -1
		test/event.symbol == sym
		test.isinstance(params['source-file'], str)

def test_failure(test):
	"""
	# - &python.failure
	"""

	f = None
	try:
		stack_5(1)
	except Exception as e:
		f = python.failure(e, e.__traceback__)

	test.isinstance(f, types.Failure)
	test.isinstance(f.f_parameters['stack-trace'], types.Trace)

def test_contextmessage(test):
	msg = python.contextmessage('WARNING', "no such message")
	test.isinstance(msg, types.Message)
	test.isinstance(msg.msg_event, types.EStruct)
	test/"no such message" == msg.msg_event.abstract
	test/'WARNING' == msg.msg_event.symbol

def test_Signal(test):
	f = None
	try:
		stack_5(1)
	except Exception as e:
		f = python.failure(e, e.__traceback__)

	sig = python.Signal(f)
	test.isinstance(str(sig), str)
