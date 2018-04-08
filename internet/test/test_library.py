from .. import library

def test_nothing(test):
	pass

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules['__name__'])
