"""
# Check serialization and parsing of frames.
"""
from .. import frames as module

def test_identifier_set_limits(test):
	"""
	# - &module.type_codes
	"""
	test/max(map(ord, set(''.join(module.type_codes.keys())))) <= 0xFFFF

def test_code_conversion(test):
	"""
	# - &module.type_integer_code
	# - &module.type_identifier_string
	"""
	for k in module.type_codes:
		icode = module.type_integer_code(k)
		idstr = module.type_identifier_string(icode)
		test/idstr == k
		fst, snd = map(ord, k)
		test/hex(icode) == (hex(fst) + hex(snd)[2:].rjust(4, "0"))

def test_unpack_unstructured(test):
	"""
	# - &module.unpack
	"""

	channel, msg = module.unpack(None, "[!# ERROR: error message]\n")
	test/channel == None
	test/msg.msg_parameters['envelope-fields'] == ["ERROR:", "error", "message"]

	channel, msg = module.unpack(None, "[!# ERROR: error message (chan:)]\n")
	test/channel == 'chan'
	test/msg.msg_parameters['envelope-fields'] == ["ERROR:", "error", "message"]

	channel, msg = module.unpack(None, "[!# ERROR: error message (chan-no-colon)]\n")
	test/channel == 'chan-no-colon'
	test/msg.msg_parameters['envelope-fields'] == ["ERROR:", "error", "message"]

def test_unpack_unstructured_channel_escape(test):
	"""
	# - &module.unpack
	"""

	channel, msg = module.unpack(None, "[!# ERROR: error message (chan) ]\n")
	test/channel == None
	test/msg.msg_parameters['envelope-fields'] == ["ERROR:", "error", "message", "(chan)"]

def test_frame_reference_data(test):
	"""
	# - &module
	"""
	from .. import types

	readframe, writeframe = module.stdio()
	data = "a raw string"

	msg = types.Message.from_string_v1(
		"message-application[!#]: render envelope message",
	)
	msg.msg_parameters['data'] = data

	s = writeframe((None, msg))
	channel, out_msg = readframe(s)

	test/channel == None
	test/('&' in s) == True
	test/out_msg.msg_parameters["data"] == data

def test_frame_structured(test):
	"""
	# - &module
	"""
	from .. import types

	readframe, writeframe = module.stdio()

	msg = types.Message.from_arguments_v1(
		None,
		types.EStruct.from_fields_v1(
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
			protocol=module.protocol,
		),
	)

	s = writeframe((None, msg))
	channel, out_msg = readframe(s)

	test/channel == None
	test/s[:4] == "[!# "
	suffix = module._tty_data_extension + module._tty_exit_extension
	test/s.endswith(" render envelope message%s]\n" %(suffix,)) == True

def test_frame_data_extension(test):
	"""
	# - &module
	"""
	from .. import types

	readframe, writeframe = module.stdio()

	failure = types.Failure.from_arguments_v1(
		None, types.EStruct.from_fields_v1(
			protocol="TFP",
			symbol="ERROR",
			abstract="internal abstract",
			identifier="TE1",
			code=1
		),
	)

	msg = types.Message.from_arguments_v1(
		None,
		types.EStruct.from_fields_v1(
			protocol="TMP",
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
		),
		data = failure
	)

	s = writeframe((None, msg))
	channel, out_msg = readframe(s)

	test/channel == None
	test/out_msg.msg_parameters["data"] == failure

def test_frame_channel_only(test):
	"""
	# - &module
	"""
	from .. import types

	readframe, writeframe = module.stdio()

	msg = types.Message.from_arguments_v1(
		None,
		types.EStruct.from_fields_v1(
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
			protocol=module.protocol,
		),
	)

	s = writeframe(('test-channel', msg))
	channel, out_msg = readframe(s)

	test/channel == 'test-channel'
	test/s[:4] == "[!# "
	signal = ''.join(module._tty_extension_signal)
	suffix = module._tty_data_extension + "" + module._tty_exit_extension
	test/s.endswith(" render envelope message (test-channel%s%s)]\n" %(signal, suffix,)) == True

def test_frame_failure_snapshot(test):
	"""
	# - &module

	# Message.from_string_v1("ENOENT[intid]: abstract", parameters={}, protocol="...", context="...")
	# Validate [>< ...] failure expectations.
	"""
	from .. import types

	readframe, writeframe = module.stdio()
	channel, msg = readframe("[>< exit summary]\n")
	f = types.Failure.from_arguments_v1(
		None,
		types.EStruct.from_fields_v1(
			protocol="test",
			symbol="ERR_TEST",
			identifier="7",
			code=7,
		), **{
			'failure-data': "<data>",
			'failure-data-sequence': list(range(10)),
		}
	)
	msg.msg_parameters['data'] = f

	msgstr = writeframe((None, msg))
	test/msgstr.startswith("[>< ") == True

	outchannel, outmsg = readframe(msgstr)
	test/outmsg.msg_event.identifier == "><"
	test/outmsg.msg_event.code == msg.msg_event.code

	fdata = outmsg.msg_parameters['data'].f_parameters
	test/fdata['failure-data'] == "<data>"
	test/fdata['failure-data-sequence'] == list(range(10))

def test_message_qualification(test):
	"""
	# - &module.message_qualification
	"""

	n = module.message_qualification(["nothing"])
	test/n == None

	n = module.message_qualification(["QUAL:", "nothing"])
	test/n == "QUAL:"

def test_message_subject_field(test):
	"""
	# - &module.message_subject_field
	"""

	n = module.message_subject_field(["nothing"])
	test/n == None

	n = module.message_subject_field(["(/path/to/resource/)", "second"])
	test/n == "(/path/to/resource/)"

def test_message_directed_areas(test):
	"""
	# - &module.message_directed_areas
	"""

	n = module.message_directed_areas(["nothing"], 0, 1)
	test/n == None

	for a in ("->", "<-", "<->"):
		n = module.message_directed_areas(["nothing", a, "something"], 0, 3)
		test/n == (a, slice(0, 1), slice(2, 3))

	for a in ("->", "<-", "<->"):
		n = module.message_directed_areas(["nothing", "something", a], 0, 3)
		test/n == (a, slice(0, 2), slice(3, 3))

	for a in ("->", "<-", "<->"):
		n = module.message_directed_areas([a, "nothing", "something"], 0, 3)
		test/n == (a, slice(0, 0), slice(1, 3))

def test_declaration_constructor(test):
	"""
	# - &module.declaration
	"""
	unpack, pack = module.stdio()
	std = module.declaration()
	test/std == module.tty_notation_1_message

	# Check compression override and format default.
	lzma = module.declaration(compression='lzma')
	channel, siom = unpack(pack((None, lzma)))
	test/channel == None
	test/siom.msg_parameters['envelope-fields'][-1] == 'base64/lzma'

	# Check format override and compression default.
	lzma = module.declaration(format='hex')
	channel, siom = unpack(pack((None, lzma)))
	test/channel == None
	test/siom.msg_parameters['envelope-fields'][-1] == 'hex/deflate'

def test_declaration_constructor_data(test):
	"""
	# - &module.declaration
	"""
	unpack, pack = module.stdio()

	# Check format override and compression default.
	dp = module.types.Parameters.from_nothing_v1()
	dp['key'] = 'value'
	withdata = module.declaration(data=dp)
	channel, siom = unpack(pack((None, withdata)))
	test/channel == None
	test/siom.msg_parameters['data']['key'] == 'value'

if __name__ == '__main__':
	from ...test import library as libtest
	import sys; libtest.execute(sys.modules[__name__])
