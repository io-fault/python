"""
Variants of the file systems interfaces yielding UNIX timestamps.
"""
import os
from . import library

def convert_stat(stat, _open = library.open.unix(library.Timestamp)):
	return stat.__class__(stat[:-3] + tuple([_open(x) for x in stat[-3:]]))

def fstat(fileno, f = os.fstat, xf = convert_stat):
	"""
	Call to :py:obj:`os.fstat` transforming local UNIX times into
	:py:class:`.library.Timestamp` instances relative to UTC.
	"""
	return xf(f(fileno))

def stat(path, f = os.stat, xf = convert_stat):
	"""
	Call to :py:obj:`os.stat` transforming local UNIX times into
	:py:class:`.library.Timestamp` instances relative to UTC.
	"""
	return xf(f(path))

def lstat(path, f = os.lstat, xf = convert_stat):
	"""
	Call to :py:obj:`os.lstat` transforming local UNIX times into
	:py:class:`.library.Timestamp` instances relative to UTC.
	"""
	return xf(f(path))
