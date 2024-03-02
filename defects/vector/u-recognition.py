"""
# Test argument vector parsing in &.recognition.
"""
import functools

from ...vector.recognition import merge, legacy, UsageViolation

def test_merge_operations(test):
	"""
	# - &merge

	# Check the default merge operations supported by &.recognition.operations.
	"""
	#! field-replace
	d = {'original': 'old'}
	merge(d, [('field-replace', 'original', 'new', -1)])
	test/d['original'] == 'new'

	#! sequence-append
	d = {'list': ['first']}
	merge(d, [
		('sequence-append', 'list', 'second', -1),
		('sequence-append', 'list', 'third', -2),
	])
	test/d['list'] == ['first', 'second', 'third']

	#! set-add
	d = {'set': set(['first'])}
	merge(d, [
		('set-add', 'set', 'second', -1),
		('set-add', 'set', 'third', -2),
		('set-add', 'set', 'third', -3),
	])
	test/d['set'] == {'first', 'second', 'third'}

	#! integer-add
	d = {}
	merge(d, [('integer-add', 'value', 2, -1),])
	test/d['value'] == 2
	merge(d, [
		('integer-add', 'value', 1, -1),
		('integer-add', 'value', 5, -1),
		('integer-add', 'value', '-1', -1),
	])
	test/d['value'] == 7

	#! subfield-replace
	d = {'inner': {}}
	merge(d, [
		('subfield-replace', 'inner', 'ifield=ivalue', -1),
	])
	test/d['inner']['ifield'] == 'ivalue'

	#! sequence-append-assignment
	d = {'seq': []}
	merge(d, [
		('sequence-append-assignment', 'seq', 'ifield=ivalue', -1),
	])
	test/d['seq'][0] == ('ifield', 'ivalue')

def test_merge_usage_violations(test):
	"""
	# - &merge

	# Check the &UsageViolation exceptions raised by &merge.
	"""
	d = {}
	merger = (lambda x: functools.partial(merge, d, [x]))
	test/UsageViolation ^ merger(('mismatch-unrecognized', '-x', None, 0))
	test/UsageViolation ^ merger(('mismatch-parameter-required', '-X', [], 0))
	test/UsageViolation ^ merger(('mismatch-parameter-restricted', '-z', 'given-param', 0))

def test_merge_interpreter_exceptions(test):
	"""
	# - &merge

	# Check the chaining of interpeter exceptions.
	"""
	class ParseError(Exception):
		@classmethod
		def raised(Class, *a):
			i = Class(*a)
			raise i

		def __init__(self, k, v):
			self.k = k
			self.v = v

	#! Check that __cause__ is set.
	d = {}
	try:
		merge(d, [('field-replace', 'slot-id', 'not-a-decimal', 0)], Interpreter=ParseError.raised)
	except UsageViolation as uv:
		test.isinstance(uv.__cause__, ParseError)
		pe = uv.__cause__
		test/pe.v == 'not-a-decimal'
	else:
		test.fail("expected UsageViolation")

def test_legacy_restricted(test):
	"""
	# - &legacy

	# Validate options that restrict parameters.
	"""
	res = {
		'-h': ('action-id', "DefaultValue", 'help-signal'),
		'--help': ('action-id', "DefaultValueLong", 'help-signal-long'),
	}

	#! Single short default.
	first, last = legacy(res, {}, ['-h'])
	test/first == ('action-id', 'help-signal', "DefaultValue", 0)
	test/last == ('remainder', None, [], 1)

	#! Single long default.
	first, last = legacy(res, {}, ['--help'])
	test/first == ('action-id', 'help-signal-long', "DefaultValueLong", 0)
	test/last == ('remainder', None, [], 1)

	#! Long and short.
	first, second, last = legacy(res, {}, ['--help', '-h'])
	test/first == ('action-id', 'help-signal-long', "DefaultValueLong", 0)
	test/second == ('action-id', 'help-signal', "DefaultValue", 1)
	test/last == ('remainder', None, [], 2)

def test_legacy_required(test):
	"""
	# - &legacy

	# Validate options that require parameters.
	"""
	req = {
		'-O': ('action-id', 'parameterized-option'),
		'--option': ('action-id', 'parameterized-option-long'),
	}

	#! Isolated.
	first, last = legacy({}, req, ['-O', "Value"])
	test/first == ('action-id', 'parameterized-option', "Value", 1)
	test/last == ('remainder', None, [], 2)

	#! Joined.
	first, last = legacy({}, req, ['-OJoinedValue'])
	test/first == ('action-id', 'parameterized-option', "JoinedValue", 0)
	test/last == ('remainder', None, [], 1)

	#! Long.
	first, last = legacy({}, req, ['--option=LongValue'])
	test/first == ('action-id', 'parameterized-option-long', "LongValue", 0)
	test/last == ('remainder', None, [], 1)

	#! Long and short.
	first, second, last = legacy({}, req, ['-OPair', '--option=LongValue'])
	test/first == ('action-id', 'parameterized-option', "Pair", 0)
	test/second == ('action-id', 'parameterized-option-long', "LongValue", 1)
	test/last == ('remainder', None, [], 2)

def test_legacy_trap(test):
	"""
	# - &legacy

	# Validate the trap case for long options.
	"""
	req = {
		'--option': ('action-id', 'parameterized-option-long'),
	}

	#! Long.
	first, second, last = legacy({}, req, ['--option=LongValue', '--k=v'], trap='trapped')
	test/first == ('action-id', 'parameterized-option-long', "LongValue", 0)
	test/second == ('sequence-append', 'trapped', ('k', 'v'), 1)
	test/last == ('remainder', None, [], 2)

def test_legacy_violations(test):
	"""
	# - &legacy

	# Validate that the expected violations are generated.
	"""
	req = {
		'-R': ('action-id', 'require-parameter'),
	}
	res = {
		'--restrict': ('action-id', 'restrict-parameter'),
	}

	#! Unrecognized.
	first, last = legacy(res, req, ['-x' 'data'])
	test/first == ('mismatch-unrecognized', '-x', None, 0)
	test/last == ('remainder', None, [], 1)

	#! Required.
	first, last = legacy(res, req, ['-R'])
	test/first == ('mismatch-parameter-required', '-R', ['require-parameter'], 0)
	test/last == ('remainder', None, [], 1)

	#! Restricted.
	first, last = legacy(res, req, ['--restrict=arg'])
	test/first == ('mismatch-parameter-restricted', '--restrict', 'arg', 0)
	test/last == ('remainder', None, [], 1)
