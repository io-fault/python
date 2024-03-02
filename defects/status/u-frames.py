"""
# Check serialization and parsing of frames.
"""
from ...status import frames as module

def io(frame) -> module.types.Frame:
	return module.structure(module.sequence(frame))

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
	# - &module.structure
	"""

	msg = module.structure("[!# ERROR: error message]\n")
	test/msg.f_image == "ERROR: error message"

	msg = module.structure("[!# ERROR: error message (chan:)]\n")
	test/msg.f_image == "ERROR: error message"

	msg = module.structure("[!# ERROR: error message (chan-no-colon)]\n")
	test/msg.f_image == "ERROR: error message"

def test_unpack_unstructured_channel_escape(test):
	"""
	# - &module.unpack
	"""

	msg = module.structure("[!# ERROR: error message (chan) ]\n")
	test/msg.f_channel == None
	test/msg.f_image == "ERROR: error message (chan)"

def test_frame_structured(test):
	"""
	# - &module
	"""
	from ...status import types

	msg = types.Frame((
		None,
		types.EStruct.from_fields_v1(
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
			protocol=module.protocol,
		),
		None,
	))

	s = module.sequence(msg)
	out_msg = module.structure(s)

	test/out_msg.f_channel == None
	test/s[:4] == "[!# "
	suffix = ""
	test/s.endswith(" render envelope message%s]\n" %(suffix,)) == True

def test_frame_data_extension(test):
	"""
	# - &module
	"""
	from ...status import types

	msg = types.Frame((
		None,
		types.EStruct.from_fields_v1(
			protocol="TMP",
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
		),
		{
			'k0': [''],
			'k1': ['value'],
			'k2': ['v1', 'v2'],
		},
	))

	s = module.sequence(msg)
	out_msg = module.structure(s)

	test/out_msg.f_channel == None
	test/out_msg.f_extension['k0'] == ['']
	test/out_msg.f_extension['k1'] == ['value']
	test/out_msg.f_extension['k2'] == ['v1', 'v2']
	test/out_msg.f_event.abstract == msg.f_event.abstract

def test_frame_channel_only(test):
	"""
	# - &module
	"""
	from ...status import types

	msg = types.Frame((
		'test-channel',
		types.EStruct.from_fields_v1(
			symbol="message-application",
			abstract="render envelope message",
			identifier="!#",
			code=module.type_integer_code("!#"),
			protocol=module.protocol,
		),
		None,
	))

	s = module.sequence(msg)
	out_msg = module.structure(s)
	test/out_msg.f_channel == 'test-channel'

	'test-channel' in test/s
	test/s[:4] == "[!# "
	signal = ''.join(module._tty_extension_signal)
	suffix = module._tty_open_extension + "" + module._tty_exit_extension
	test/s.endswith(" render envelope message (test-channel%s%s)]\n" %(signal, suffix,)) == True

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
	std = module.declaration()
	test/std == module.tty_notation_1_message

	# Check compression override and format default.
	lzma = module.declaration(compression='lzma')
	siom = io(lzma)
	test/siom.f_channel == None
	'base64/lzma' in test/siom.f_image

	# Check format override and compression default.
	lzma = module.declaration(format='hex')
	siom = io(lzma)
	test/siom.f_channel == None
	test/siom.f_image.split()[-1] == 'hex/deflate'
