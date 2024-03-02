from ...kernel import kills
from ...kernel import flows
from . import library as testlib

def test_fault(test):
	"""
	# Check interrupt effect of faulting.
	"""
	ctx, s = testlib.sector()
	f = kills.Fatal()
	f1 = flows.Channel()
	s.dispatch(f1)
	s.dispatch(f)
	ctx.flush()
	test/f1.interrupted == True
	test/s.interrupted == True
	test/bool(f.exceptions) == True
