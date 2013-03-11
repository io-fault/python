"""
Variants of the file systems interfaces yielding UNIX timestamps.
"""
import os
from . import lib

def convert_stat(stat, _open = lib.open.unix(lib.Timestamp)):
	return stat.__class__(stat[:-3] + tuple([_open(x) for x in stat[-3:]]))

def fstat(fileno, f = os.fstat, xf = convert_stat):
	"""
	fstat(fileno)

	Call to :py:obj:`os.fstat` transforming local UNIX times into
	:py:class:`rhythm.lib.Timestamp` instances relative to UTC.
	"""
	return xf(f(fileno))

def stat(path, f = os.stat, xf = convert_stat):
	"""
	stat(path)

	Call to :py:obj:`os.stat` transforming local UNIX times into
	:py:class:`rhythm.lib.Timestamp` instances relative to UTC.
	"""
	return xf(f(path))

def lstat(path, f = os.lstat, xf = convert_stat):
	"""
	lstat(path)

	Call to :py:obj:`os.lstat` transforming local UNIX times into
	:py:class:`rhythm.lib.Timestamp` instances relative to UTC.
	"""
	return xf(f(path))
