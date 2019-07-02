from .. import sysclock as module
from .. import types

def test_now(test):
	test.isinstance(module.now(), types.Timestamp)

def test_elapsed(test):
	test.isinstance(module.elapsed(), types.Measure)
