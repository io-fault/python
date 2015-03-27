from .. import lib

def test_nothing(test):
	pass

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules['__name__'])
