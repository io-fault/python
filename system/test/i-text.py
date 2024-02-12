import sys
from .. import text as module

def test_setlocale(test):
	"""
	# - &.extensions.text/module.c#dsetlocale
	# - &module.setlocale
	"""
	import locale
	test/module.setlocale() == locale.setlocale(locale.LC_ALL, "")

def test_encoding(test):
	locale = module.setlocale()
	module.encoding() in test/locale
