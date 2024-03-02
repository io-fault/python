from ...context import weak as module

class Referenced(object):
	def method(self, *args, **kw):
		return (args, kw)

instance = Referenced()

def test_zero(test):
	test/module.Method(instance.method).zero() == ((), {})

def test_one(test):
	test/module.Method(instance.method).one(1) == ((1,), {})

def test_any(test):
	test/module.Method(instance.method).any(2, 1) == ((2, 1), {})

def test_keywords(test):
	test/module.Method(instance.method).keywords("A", k="v") == (("A",), {"k":"v"})

def test_lost_target(test):
	i = Referenced()
	w = module.Method(i.method)
	test/w.zero() == ((), {})
	del i

	# Probably should be a ReferenceError, but testing
	# a __call__ implementation that did increased the
	# call overhead by about 50%. (timeit, 2019)
	test/ReferenceError ^ w.zero
	test/ReferenceError ^ (lambda: w.one(1))
	test/ReferenceError ^ w.any
	test/ReferenceError ^ w.zero
