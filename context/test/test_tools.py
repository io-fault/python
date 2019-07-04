from .. import tools as module

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

if __name__ == '__main__':
	from ...test import library as libtest
	import sys; libtest.execute(sys.modules[__name__])
