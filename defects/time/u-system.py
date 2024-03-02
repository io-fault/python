from ...time import system as module
from ...time import types

def test_utc(test):
	"""
	# - &module.utc
	"""
	test.isinstance(module.utc(), types.Timestamp)

def test_elapsed(test):
	"""
	# - &module.elapsed
	"""
	test.isinstance(module.elapsed(), types.Measure)

def test_zone_local(test):
	"""
	# - &module.local
	"""
	z = module.zone()
	ts = module.utc()
	lt, offset = z.localize(ts)
	test.isinstance(lt, ts.__class__)

def test_date(test):
	"""
	# - &module.date
	"""
	test.isinstance(module.date(), module.types.Date)
	test.isinstance(module.date(-1), module.types.Date)
	test.isinstance(module.date(+1), module.types.Date)
