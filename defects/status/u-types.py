"""
# Majority of tests here revolve around parameters. The other classes in &types
# are mostly simple dataclasses only needing constructor and property sanity checks.
"""
from ...status import types

def test_EStruct_constructors_v1(test):
	"""
	# - &types.EStruct.from_fields_v1
	# - &types.EStruct.from_arguments_v1
	# - &types.EStruct.from_tuple_v1
	"""
	# Check defaults.
	ambiguous = types.EStruct.from_fields_v1('protocol-field')
	test/ambiguous.protocol == 'protocol-field'
	test/ambiguous.code == 0
	test/ambiguous.symbol == "Unspecified"
	test/ambiguous.identifier == ""

	ambiguous = types.EStruct.from_fields_v1('protocol-field-2')
	test/ambiguous.protocol == 'protocol-field-2'

	# Check keywords.
	specific = types.EStruct.from_fields_v1(
		'posix/errno', # Not a keyword; required positional.
		identifier='1', code=1,
		symbol='EAGAIN',
		abstract="system call says try again later",
	)
	test/specific.protocol == 'posix/errno'
	test/specific.code == 1
	test/specific.identifier == '1'
	test/specific.symbol == "EAGAIN"

	# Forced trim.
	test/len(types.EStruct.from_tuple_v1(list(range(6)))) == 5

	# Comparison with construct from fields_v1
	exact = types.EStruct.from_arguments_v1(*specific)
	test/specific == exact

	# Again, but using from_tuple
	exact = types.EStruct.from_tuple_v1(specific)
	test/specific == exact

def test_EStruct_immutable(test):
	"""
	# Warning test; just a notification of unexpected behaviour.
	"""
	estruct = types.EStruct.from_fields_v1('protocol-field')

	test/AttributeError ^ (lambda: estruct.__setattr__('code', -1))
	for x in ('protocol', 'identifier', 'symbol', 'abstract'):
		test/AttributeError ^ (lambda: estruct.__setattr__(x, 'rejected-value'))

def test_Frame_constructors_v1(test):
	"""
	# - &types.Frame.from_event_v1
	# - &types.Frame.f_event
	# - &types.Frame.f_extension
	"""
	esa = types.EStruct.from_fields_v1('protocol-field')
	f = types.Frame.from_event_v1(esa, None, None)

	test/f.f_event == esa
	test/bool(f.f_extension) == False
	test/f.f_channel == None

def test_string_constructor(test):
	"""
	# - &types.EStruct.from_string_v1
	# - &types.Frame.from_string_v1
	"""

	typset = [types.Frame]
	for Class in typset:
		packet = Class.from_string_v1("QUAL[200]: abstract")
		test.isinstance(packet, Class)

		ev = packet.f_event
		test/ev.identifier == "200"
		test/ev.code == 200
		test/ev.abstract == "abstract"
