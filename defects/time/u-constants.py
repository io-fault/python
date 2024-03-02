"""
# Sanity checks regarding presence.
"""
from ...time import constants as module

def test_indefinites(test):
	test/module.never > module.always
	test/module.never > module.whenever
	test/module.always < module.whenever
	test/module.always < module.never

	test/module.infinity > module.zero

	test/module.never == module.never
	test/-module.never == module.always
	test/module.always == module.always
	test/-module.always == module.never
	test/module.whenever == module.whenever
	test/module.zero == module.zero

	# Check negative eternity.
	test/-module.infinity == (module.infinity.__class__(-1))

def test_datums(test):
	test/module.local_datum == 0
	test.isinstance(module.unix_epoch, module.local_datum.__class__)

def test_annum_value(test):
	test/module.annum > 0

def test_indefinite_representations(test):
	test/repr(module.never) == '(time.never)'
	test/repr(module.always) == '(time.always)'
	test/repr(module.whenever) == '(time.whenever)'

	test/str(module.never) == 'never'
	test/str(module.always) == 'always'
	test/str(module.whenever) == 'whenever'

def test_eternals_representations(test):
	test/repr(module.infinity) == '(time.infinity)'
	test/repr(-module.infinity) == '(-time.infinity)'
	test/repr(module.zero) == '(time.zero)'

	test/str(module.infinity) == 'infinity'
	test/str(-module.infinity) == '-infinity'
	test/str(module.zero) == '0'
