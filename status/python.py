"""
# Tools for building status data from Python exceptions, tracebacks, and frames.
"""
import sys
import linecache
import typing

from . import types

exception_protocol = 'http://if.fault.io/status/python/exception'
message_protocol = 'http://if.fault.io/status/python/message'
frame_protocol = 'http://if.fault.io/status/python/frames/'

def iterstack(frame):
	"""
	# Construct a generator producing frame-lineno pairs from a stack of frames.
	"""
	f = frame
	while f is not None:
		yield (f, f.f_lineno)
		f = f.f_back

def itertraceback(traceback):
	"""
	# Construct a generator producing frame-lineno pairs from a traceback.
	"""
	tb = traceback
	while tb is not None:
		yield (tb.tb_frame, tb.tb_lineno)
		tb = tb.tb_next

def iterlnotab(lineno:int, encoded:bytes) -> typing.Iterable[typing.Tuple[int, int]]:
	# Construct bytecode address to line number pairs from an encoded co_lnotab field.
	# Currently not used and may be deprecated.
	ln = lineno
	ba = 0

	for ba_i, ln_i in zip(encoded[0::2], encoded[1::2]):
		ba += ba_i
		ln += ln_i
		yield ba, ln

def traceframes(frameiter, Class=types.Trace):
	"""
	# Construct a &types.Trace instance using an iterator of Python frames and line numbers.
	# Normally, used with &iterstack or &itertraceback.
	"""
	from linecache import getline
	mkevent = types.EStruct.from_fields_v1
	mkparam = types.Parameters.from_nothing_v1

	events = []
	add = events.append

	for f, lineno in frameiter:
		co = f.f_code

		symlineno = co.co_firstlineno
		symbol = co.co_name
		fpath = co.co_filename
		f_locals = f.f_locals
		f_globals = f.f_globals

		event = mkevent(
			frame_protocol + f_globals['__name__'],
			identifier=str(lineno),
			code=lineno,
			symbol=symbol,
			abstract=getline(fpath, lineno)
		)

		fp = mkparam()
		fp.set_system_file('source-file', fpath)
		add((event, fp))

	return Class((events,))

def failure(exception, traceback, context=None, EConstruct=types.EStruct.from_fields_v1):
	"""
	# Create a &types.Failure instance from a Python exception instance and traceback.
	"""
	error = EConstruct(
		exception_protocol,
		identifier='',
		code=0,
		symbol=type(exception).__name__,
		abstract=str(exception)
	)

	t = traceframes(itertraceback(traceback))
	p = types.Parameters.from_specifications_v1([
		('value', 'trace', 'stack-trace', t)
	])
	if context is None:
		context = types.Trace(([],))

	return types.Failure((error, p, context))

def contextmessage(severity, message, context=None,
		EConstruct=types.EStruct.from_fields_v1,
	):
	"""
	# Create a &types.Message instance with a stack trace contained in its parameters.

	# ! WARNING: Implementation is incomplete; no process or system context is provided.
	"""
	msg = EConstruct(
		message_protocol,
		identifier='',
		code=0,
		symbol=severity,
		abstract=message
	)

	t = traceframes(iterstack(sys._getframe().f_back))
	p = types.Parameters.from_specifications_v1([
		('value', 'trace', 'stack-trace', t)
	])
	if context is None:
		context = types.Trace(([],))

	return types.Message((msg, p, context))

class Signal(Exception):
	"""
	# Failure signal exception.

	# Exception Container for &types.Failure instances intended to represent the error.
	"""

	def __init__(self, failure:types.Failure):
		self._args = (failure,)
		self._f_failure = failure

	def __str__(self):
		ev = self._f_failure.f_error
		return ("(%s %r)" %(ev.symbol, ev.abstract))
