"""
# Majority of tests here revolve around parameters. The other classes in &types
# are mostly simple dataclasses only needing constructor and property sanity checks.
"""
from .. import types

def test_EStruct_constructors_v1(test):
	"""
	# - types.EStruct.from_fields_v1
	# - types.EStruct.from_arguments_v1
	# - types.EStruct.from_tuple_v1
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
	# - types.Failure.from_arguments_v1
	# - types.Failure.f_error
	# - types.Failure.f_context
	# - types.Failure.f_parameters
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
	# - types.Message.from_arguments_v1
	# - types.Message.msg_event
	# - types.Message.msg_context
	# - types.Message.msg_parameters
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
	# - types.Report.from_arguments_v1
	# - types.Report.r_event
	# - types.Report.r_context
	# - types.Report.r_parameters
	"""
	esa = types.EStruct.from_fields_v1('protocol-field')

	re = types.Report.from_arguments_v1(
		types.Trace.from_nothing_v1(), esa,
	)

	test/re.r_event == esa
	test/re.r_context.t_route == []
	test/re.r_parameters.empty() == True

if __name__ == '__main__':
	from ...test import library as libtest
	import sys; libtest.execute(sys.modules[__name__])
