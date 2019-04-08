"""
# Check the &library.Relay, &library.Receiver, and &library.Inlet types.
"""
from .. import library as testlib
from ... import flows as library
from ... import io

def test_Receiver(test):
	ctx, S = testlib.sector()
	c = library.Collection.list()
	r = library.Receiver()
	r.f_connect(c)
	S.dispatch(c)
	S.dispatch(r)
	r.f_transfer(1)
	test/c.c_storage == [1]

	r.f_terminate()
	test/r.terminated == True
	test/c.terminated == True

def test_Relay(test):
	ctx, S = testlib.sector()
	r = library.Receiver()
	re = library.Relay(r, None)

	c = library.Collection.list()
	r.f_connect(c)

	S.dispatch(c)
	S.dispatch(r)
	S.dispatch(re)
	re.f_transfer(1)

	test/c.c_storage == [1]
	re.f_terminate()
	test/r.terminated == True
	test/re.terminated == True
	test/c.terminated == True

def test_Relay_interrupt(test):
	ctx, S = testlib.sector()
	r = library.Receiver()
	re = library.Relay(r, None)

	c = library.Collection.list()
	r.f_connect(c)

	S.dispatch(c)
	S.dispatch(r)
	S.dispatch(re)
	re.interrupt()
	re.f_transfer(1)

	test/c.c_storage == []
	test/r.interrupted == True
	test/re.interrupted == True
	test/c.interrupted == False

def test_Inlet(test):
	ctx, S = testlib.sector()

	c = library.Collection.list()
	r = library.Receiver()
	r.f_connect(c)
	i = library.Inlet(r, None)

	S.dispatch(c)
	S.dispatch(r)
	S.dispatch(i)
	i.f_transfer(1)

	test/c.c_storage == [1]
	i.f_terminate()
	test/i.terminated == True
	test/r.terminated == True
	test/c.terminated == True
