"""
# Sanity checks regarding presence.
"""
from .. import constants as module

def test_indefinites(test):
	test/module.never > module.genesis
	test/module.never > module.present
	test/module.genesis < module.present
	test/module.genesis < module.never

	test/module.never == module.never
	test/module.genesis == module.genesis
	test/module.present == module.present

	module.never in test/module.continuum
	module.genesis in test/module.continuum
	module.present in test/module.continuum

def test_datums(test):
	test/module.local_datum == 0
	test.isinstance(module.unix_epoch, module.local_datum.__class__)

def test_annum_value(test):
	test/module.annum > 0
