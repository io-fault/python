"""
Variants of the file systems interfaces yielding UNIX timestamps.
"""
import os
from . import library

def convert_stat(stat, _open = library.open.unix(library.Timestamp)):
	return stat.__class__(stat[:-3] + tuple([_open(x) for x in stat[-3:]]))

def fstat(fileno, f = os.fstat, xf = convert_stat):
	"""
	Call to &os.fstat transforming local UNIX times into
	&.library.Timestamp instances relative to UTC.
	"""
	return xf(f(fileno))

def stat(path, f = os.stat, xf = convert_stat):
	"""
	Call to &os.stat transforming local UNIX times into
	&.library.Timestamp instances relative to UTC.
	"""
	return xf(f(path))

def lstat(path, f = os.lstat, xf = convert_stat):
	"""
	Call to &os.lstat transforming local UNIX times into
	&.library.Timestamp instances relative to UTC.
	"""
	return xf(f(path))
