from ...context import match as module

sample = [
	'http://fault.io/src/',
	'http://fault.io/src/project/',
]

def search_test(test, ss):
	test/ss['http://fault.io/src/pkg'] == 'http://fault.io/src/'
	test/ss['http://fault.io/src/project/python'] == 'http://fault.io/src/project/'
	# exact prefix match
	test/ss['http://fault.io/src/project/'] == 'http://fault.io/src/project/'

	test/KeyError ^ (lambda: ss['noprefix'])
	test/tuple(ss.matches('noprefix')) == ()
	test/ss.get('noprefix', 'default') == 'default'
	test/('noprefix' in ss) == False
	test/set(ss.values()) == ss.sequences

def test_SubsequenceScan_matches(test):
	ss = module.SubsequenceScan(sample)
	search_test(test, ss)

def test_SubsequenceScan_ascending(test):
	# check reverse order; longest should never have first match...
	ss = module.SubsequenceScan(sample, order=False)
	test/ss['http://fault.io/src/project/python'] == 'http://fault.io/src/'
	test/list(ss.matches('http://fault.io/src/project/python')) == sample

def test_SubsequenceScan_deltas(test):
	ss = module.SubsequenceScan(sample)
	ss.discard('http://fault.io/src/')

	try:
		search_test(test, ss)
	except:
		pass
	else:
		test.fail("search test passed with missing entry")

	ss.add('http://fault.io/src/')
	search_test(test, ss) # Re-introduced missing entry.
