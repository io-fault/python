from .. import match as module

def search_test(test, Type):
	prefixes = [
		'http://fault.io/src/',
		'http://fault.io/src/project/',
	]

	strset = Type(prefixes)
	test/strset['http://fault.io/src/pkg'] == 'http://fault.io/src/'
	test/strset['http://fault.io/src/project/python'] == 'http://fault.io/src/project/'
	# exact prefix match
	test/strset['http://fault.io/src/project/'] == 'http://fault.io/src/project/'

	test/KeyError ^ (lambda: strset['noprefix'])
	test/tuple(strset.matches('noprefix')) == ()
	test/strset.get('noprefix', 'default') == 'default'
	test/('noprefix' in strset) == False
	test/set(strset.values()) == strset.sequences

	# check reverse order; longest should never have first match...
	strset = Type(prefixes, order=False)
	test/strset['http://fault.io/src/project/python'] == 'http://fault.io/src/'
	test/list(strset.matches('http://fault.io/src/project/python')) == prefixes

def test_SubsequenceScan(test):
	search_test(test, module.SubsequenceScan)

if __name__ == '__main__':
	from ...test import library as libtest; import sys
	libtest.execute(sys.modules[__name__])
