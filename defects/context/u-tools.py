import dataclasses
from ...context import tools as module

def test_struct(test):
	"""
	# Validate that struct provides the expected defaults for &dataclasses.dataclass.
	"""
	@module.struct()
	class T:
		a: int
		b: str

	t = T(a=1, b="s")
	test/t.a == 1
	test/t.b == "s"

	test/dataclasses.FrozenInstanceError ^ (lambda: setattr(t, "a", 2))
	test/t == T(a=1, b="s")

def test_compose(test):
	function = module.compose
	f1 = (lambda x: x + ': suffix:')
	f2 = (lambda x: 'prefix: ' + x)
	f3 = (lambda x: 'different: ' + x)

	cf = function(f1, f2)
	test/cf("STRING") == "prefix: STRING: suffix:"

	cf = function(f2, f2)
	test/cf("STRING") == "prefix: prefix: STRING"

	cf = function(f2, f3)
	test/cf("STRING") == "prefix: different: STRING"

	cf = function(f3, f2)
	test/cf("STRING") == "different: prefix: STRING"

def test_unroll(test):
	test/module.unroll(lambda x: x)([1,2,3]) == [1,2,3]
	test/module.unroll(lambda x: x)([]) == []

def test_unique(test):
	test/list(module.unique([1,1,2])) == [1,2]
	test/list(module.unique([2,1,1,2,2])) == [2,1]
	test/list(module.unique([2,1,1,2,2], 2)) == [1]
	test/list(module.unique([], 2)) == []

def test_sum_lengths(test):
	test/module.sum_lengths([(0,0), (), (0,0,0)]) == 5
	test/module.sum_lengths([]) == 0
	test/module.sum_lengths([(), ()]) == 0
	test/module.sum_lengths(["a", "few", "bytes"]) == len("afewbytes")

def test_consistency(test):
	p0 = []
	test/module.consistency(p0, p0) == 0

	p1 = ['root']
	test/module.consistency(p1, p1) == 1

	p2 = ['root', 'segment-1']
	p3 = ['root', 'segment-2']
	test/module.consistency(p1, p2) == 1
	test/module.consistency(p1, p3) == 1
	test/module.consistency(p1, p2) == 1
	test/module.consistency(p1, p2, p3) == 1

	p4 = ['alt', 'segment-1']
	test/module.consistency(p4, p2) == 0

	p4 = ['alt', 'segment-1']
	test/module.consistency(p2, p4) == 0

	p5 = ['alt', 'segment-1', 'segment-2']
	test/module.consistency(p5, p4) == 2

	p6 = ['alt', 'segment-1', 'segment-2', 'segment-3']
	test/module.consistency(p6, p5) == 3

	for x in [p1, p2, p3, p4, p5]:
		test/module.consistency(x, x) == len(x)
