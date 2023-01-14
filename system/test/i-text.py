import sys
from .. import text

def test_setlocale(test):
	"""
	# - &.extensions.text/module.c#dsetlocale
	# - &text.setlocale
	"""
	import locale
	test/text.setlocale() == locale.setlocale(locale.LC_ALL, "")

def test_encoding(test):
	locale = text.setlocale()
	text.encoding() in test/locale
