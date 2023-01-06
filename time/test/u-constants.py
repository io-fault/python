"""
# Sanity checks regarding presence.
"""
from .. import constants as module

def test_indefinites(test):
	test/module.never > module.always
	test/module.never > module.whenever
	test/module.always < module.whenever
	test/module.always < module.never

	test/module.eternity > module.zero

	test/module.never == module.never
	test/-module.never == module.always
	test/module.always == module.always
	test/-module.always == module.never
	test/module.whenever == module.whenever
	test/module.zero == module.zero

	module.never in test/module.continuum
	module.always in test/module.continuum
	module.whenever in test/module.continuum

	# Check negative eternity.
	test/-module.eternity == (module.eternity.__class__(-1))

def test_datums(test):
	test/module.local_datum == 0
	test.isinstance(module.unix_epoch, module.local_datum.__class__)

def test_annum_value(test):
	test/module.annum > 0
