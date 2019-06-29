"""
# Majority of tests here revolve around parameters. The other classes in &types
# are mostly simple dataclasses only needing constructor and property sanity checks.
"""
from .. import types

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

def test_Failure_constructors_v1(test):
	"""
	# - &types.Failure.from_arguments_v1
	# - &types.Failure.f_error
	# - &types.Failure.f_context
	# - &types.Failure.f_parameters
	"""
	esa = types.EStruct.from_fields_v1('protocol-field')

	failure = types.Failure.from_arguments_v1(
		types.Trace.from_nothing_v1(), esa,
	)

	test/failure.f_error == esa
	test/failure.f_context.t_route == []
	test/failure.f_parameters.empty() == True

def test_Message_constructors_v1(test):
	"""
	# - &types.Message.from_arguments_v1
	# - &types.Message.msg_event
	# - &types.Message.msg_context
	# - &types.Message.msg_parameters
	"""
	esa = types.EStruct.from_fields_v1('protocol-field')

	msg = types.Message.from_arguments_v1(
		types.Trace.from_nothing_v1(), esa,
	)

	test/msg.msg_event == esa
	test/msg.msg_context.t_route == []
	test/msg.msg_parameters.empty() == True

def test_Report_constructors_v1(test):
	"""
	# - &types.Report.from_arguments_v1
	# - &types.Report.r_event
	# - &types.Report.r_context
	# - &types.Report.r_parameters
	"""
	esa = types.EStruct.from_fields_v1('protocol-field')

	re = types.Report.from_arguments_v1(
		types.Trace.from_nothing_v1(), esa,
	)

	test/re.r_event == esa
	test/re.r_context.t_route == []
	test/re.r_parameters.empty() == True

def test_Parameters_typeform_detection(test):
	"""
	# - &types.Parameters.identify_object_typeform
	"""

	iotfx = types.Parameters.identify_object_typeform
	iotfn = [
		(lambda x: iotfx(x)[1]),
		(lambda x: iotfx([x])[1]),
		(lambda x: iotfx(set([x]))[1]),
	]

	for iotf in iotfn:
		test/iotf(None) == 'void'
		test/iotf(-1) == 'integer'
		test/iotf(1) == 'integer'
		test/iotf("string") == 'string'
		test/iotf(True) == 'boolean'
		test/iotf(False) == 'boolean'
		test/iotf(1.2) == 'rational'
		test/iotf(b'') == 'octets'

	test/iotfx({}) == ('value', 'parameters')
	test/iotfx([{}]) == ('v-sequence', 'parameters')

def test_Parameters_constructors_v1(test):
	"""
	# - &types.Parameters.from_nothing_v1
	# - &types.Parameters.from_pairs_v1
	# - &types.Parameters.from_specifications_v1
	# - &types.Parameters.from_relation_v1
	"""

	empty = types.Parameters.from_nothing_v1()
	test/empty.empty() == True
	test/set(empty.iterspecs()) == set()

	iprimitives = types.Parameters.from_pairs_v1([
		('i-field', 1),
		('s-field', "string"),
		('b-field', True),
	])

	xprimitives = types.Parameters.from_specifications_v1([
		('value', 'integer', 'i-field', 1),
		('value', 'string', 's-field', "string"),
		('value', 'boolean', 'b-field', True),
	])
	test/iprimitives == xprimitives

	rel = types.Parameters.from_relation_v1(
		['id', 'name'],
		['integer', 'string'],
		[
			(1, "first"),
			(2, "second"),
			(3, "third"),
		]
	)
	test/rel.get_parameter('id') == [1,2,3]
	test/rel.get_parameter('name') == ["first", "second", "third"]

def test_Parameters_relation_storage(test):
	tuples = [
		(1, "first"),
		(2, "second"),
		(3, "third"),
	]
	rel = types.Parameters.from_relation_v1(
		['id', 'name'],
		['integer', 'string'],
		tuples,
	)

	test/list(rel.select(None)) == tuples
	test/list(rel.select(['id', 'name'])) == tuples
	rel.insert([
		(4, "fourth"),
	])

	test/list(rel.select(['id', 'name'])) == (tuples + [(4, "fourth")])

def test_packet_string_constructor(test):
	"""
	# - &types._from_string_constructor
	# - &types.Message.from_string_v1
	# - &types.Failure.from_string_v1
	# - &types.Report.from_string_v1
	"""

	typset = [types.Message, types.Failure, types.Report]
	for Class in typset:
		packet = Class.from_string_v1("QUAL[200]: abstract")
		test.isinstance(packet, Class)

		es, params, tr = types.corefields(packet)
		test/es.identifier == "200"
		test/es.code == 200
		test/es.abstract == "abstract"

if __name__ == '__main__':
	from ...test import library as libtest
	import sys; libtest.execute(sys.modules[__name__])
