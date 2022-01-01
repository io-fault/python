"""
# Formatting and parsing tools for status frame transport envelopes.

# This module provides conceptual definitions for Status Frame events (&types.EStruct) and
# I/O operations supporting the transmission of those events.

# Status Frames are &types.Message instances that can be serialized into and parsed from a data stream.

# [ Usage ]

# The operation used to serialize and load the data extension is decoupled, so an allocation
# function is provided to apply the defaults for the data extension transport:
# #!syntax/python
	from fault.status import types, frames
	loadframe, dumpframe = frames.stdio()

# Frame envelopes may or may not have content (data extensions):
# #!syntax/python
	msg = types.Message.from_string_v1(
		"message-application[!#]: ERROR: no such resource",
		protocol=frames.protocol)
	sys.stdout.write(dumpframe((None, msg)))

	"[!# ERROR: no such resource]\n"

# Errors from a particular protocol have to be contained:
# #!syntax/python
	err = types.Failure.from_string_v1(
		"NOT FOUND[404]: no such resource",
		protocol="http://ietf.org/../http")
	msg = types.Message.from_string_v1(
		"message-application[!#]: ERROR: no such resource",
		protocol=frames.protocol)
	msg.msg_parameters['data'] = err
	sys.stdout.write(dumpframe((None, msg)))

	"[!# ERROR: no such resource (+)]" # base64 data extension omitted

# Serialized messages are expected to include the trailing newline:
# #!syntax/python
	for line in sys.stdin.readlines():
		envelope_channel, msg = loadframe(line)
		assert msg.msg_event.protocol == frames.protocol

# [ Message Types ]

# The recognized message types and their symbolic name are stored in &type_codes.

# [ Properties ]

# /Envelope/
	# Tuple type signature holding channel string and Status Frame message.

	# # &str
	# # &types.Message

# /protocol/
	# String identifying the status frames protocols.

# /ttyn1_minimum_overhead/
	# Informative minimum size regarding tty-notation-1 status frames.
"""
import typing
import functools

from . import types

# Type signature for frame messages. (channel, message)
Envelope = typing.Tuple[str, types.Message]

# Protocol identity for envelope &types.Message instances.
protocol = "http://if.fault.io/status/frames"

# Two-Character EStruct.identifier.
type_codes = {
	# [!? PROTOCOL: http://if.fault.io/status/frames tty-notation-1] (optional declaration)
	"!?": 'message-protocol',

	# Warnings, Errors, and Information with respect to some conceptual level of a frame source.
	"!#": 'message-application',
	"!*": 'message-framework',
	"!%": 'message-administrative',
	"!>": 'message-entity',

	# System processes, virtual processes, transfers, etc.
	"><": 'transaction', # Aggregate transaction event; combined start and stop.
	"<>": 'transaction-request', # [<> ...(xid)] Inverse frame: dispatch transaction.
	"->": 'transaction-started', # [-> ...(xid)]
	"--": 'transaction-event', # [-- ...(xid)] Anonymous event; arbitrary status data.
	"<-": 'transaction-stopped', # [<- ...(xid)]

	# Resource Content Manipulation
	"+=": 'resource-inserted-units', # append
	"-=": 'resource-deleted-units', # partial truncation

	# SCM Operation Reports
	"Δ=": 'resource-delta',
	"<=": 'resource-reverted',
	"==": 'resource-committed',

	# Resource Container Manipulations
	"+.": 'resource-initialized',
	"%.": 'resource-truncated',
	"-.": 'resource-deleted',

	"*.": 'resource-replicated',
	"&.": 'resource-referenced',
	"..": 'resource-relocated',
	"Δ@": 'resource-property-delta',

	">|": 'resource-rewritten',
	".|": 'resource-relocated-substitution',
	"*|": 'resource-replicated-substitution',
	"&|": 'resource-referenced-substitution',

	"*&": 'resource-hardlinked',
	"*+": 'resource-replicated-merge',

	# Archive I/O
	"^*": 'archive-extraction-replicated',
	"^|": 'archive-extraction-replicated-substitution',
	"^+": 'archive-extraction-replicated-merge',

	"√*": 'archive-delta-replicated-into',
	"√|": 'archive-delta-replicated-substitution-into',
	"√+": 'archive-delta-merged-into',
	"√-": 'archive-delta-deleted',
	"√&": 'archive-delta-referenced',

	# Transfer Snapshots.
	"↑.": 'resource-transmitted',
	"↓.": 'resource-received',
	"↑|": 'resource-transmitted-substitution',
	"↓|": 'resource-received-substitution',

	# Transfer Progress Information.
	"↑:": 'data-transmitted',
	"↓:": 'data-received',
	"↓↑": 'data-transferred',
}

@functools.lru_cache(16)
def type_integer_code(typstring:str) -> int:
	"""
	# Convert a two-character type code symbol into an unsigned 32-bit integer.
	# Currently, only supporting unicode characters in the 16-bit range.
	"""

	fst, snd = map(ord, typstring)
	return (fst << 16) | snd

def type_identifier_string(typcode:int) -> str:
	"""
	# Convert an integer type code into the two-character string used for serialization and display.
	"""
	return ''.join(map(chr, ((typcode >> 16) & 0xFFFF, typcode & 0xFFFF)))

# Contrived OSC. While OSC's didnt't follow CSI's format, it has been seen in the wild.
# So the CSI parameter format is used to carve out a namespace for this purpose.
# First parameter is the command identifier.
# Second parameter is padding to discourage keyboard modifier identification if ever parsed.
# Third parameter is an internal channel identifier.

# OSC (internal channel 1 for field header) followed with STX.
_tty_field_lengths = "\x1b]8;1;1-x\x02"
# ST followed with backspace and space (ensure \< matches)
_tty_exit_fields = "\x1b\\\x08 "

# OSC (internal channel 2 for data extension)
_tty_data_extension = "\x1b]8;1;2-x"
# ETX followed with ST
_tty_exit_extension = "\x03\x1b\\"

# Highlight data presence indicator.
_tty_extension_signal = ("\x1b[32m", "\x1b[39m") # Green.

# Extension Signal SGR not included as it's only present if data is attached.
# This is the minimum size for frames including a header and data extension.
ttyn1_minimum_overhead = \
	len(_tty_field_lengths) + \
	len(_tty_exit_fields) + \
	len(_tty_data_extension) + \
	len(_tty_exit_extension) + \
	len("[-- ]\n")

_loaded_frame_start = "[{ts} {fieldmap}{fields}"
_loaded_frame_partition = " ({channel}{wrap[0]}{signal}{wrap[1]}{hidden}"
_loaded_frame_stop = " {reveal})]\n"
_empty_frame_stop = "{hidden}{reveal}]\n"

def pack_inner(
		transport:typing.Callable, fspec:Envelope,

		_fmt_lframe_start=_loaded_frame_start.format,
		_fmt_lframe_part=_loaded_frame_partition.format,
		_fmt_lframe_stop=_loaded_frame_stop.format,
		_fmt_eframe_stop=_empty_frame_stop.format,
		isinstance=isinstance, list=list, map=map, len=len, str=str
	) -> typing.Tuple[str, bytes, str]:
	"""
	# Pack a status frame for transmission.

	# Constructs a triple containing the leading envelope string,
	# the encoded bytes of data extending the frame and the terminating trailer.
	"""

	channel, frame = fspec
	p = frame.msg_parameters
	data = p.get('data')

	if channel:
		if data is not None:
			channel += ":"
	else:
		channel = ''

	ts = frame.msg_event.identifier
	fields = p.get('envelope-fields')

	if fields is None:
		fields = list(frame.msg_event.abstract.split())

	fmap = list(map(len, fields))
	fstr = ' '.join(fields)

	if data or channel:
		if data is None:
			signal = ""
			load = b""
		elif isinstance(data, str):
			signal = "&"
			load = data.encode('utf-8')
		else:
			assert isinstance(data, (types.Message, types.Failure, types.Report, types.Parameters))
			signal = "+"
			load = transport(data)

		partd = _fmt_lframe_part(
			channel=channel, signal=signal,
			hidden=_tty_data_extension,
			wrap=_tty_extension_signal
		)

		fmap.extend((len(partd)-2, len(load)))
		fm = _tty_field_lengths + ' '.join(map(str, fmap)) + _tty_exit_fields

		start = _fmt_lframe_start(ts=ts, fieldmap=fm, fields=fstr) + partd
		end = _fmt_lframe_stop(reveal=_tty_exit_extension)
	else:
		load = b""
		fmap.extend((0, 0)) # Zero channel area and data extension.
		fm = _tty_field_lengths + ' '.join(map(str, fmap)) + _tty_exit_fields

		start = _fmt_lframe_start(ts=ts, fieldmap=fm, fields=fstr)
		end = _fmt_eframe_stop(hidden=_tty_data_extension, reveal=_tty_exit_extension)

	return (start, load, end)

def pack(transport:typing.Callable, fspec:Envelope) -> str:
	"""
	# Pack a status frame into a &str for transmission.

	# Constructs a single &str instance.

	# [ Parameters ]

	# /transport/
		# Function used to serialize the data extension of the frame.
	# /fspec/
		# The channel-message pair to serialize.
	"""
	s1, s2, s3 = pack_inner(transport, fspec)
	return s1 + s2.decode('ascii') + s3

def _select_fields(string, offset, sizes):
	"""
	# Extract fields according to the sequences of &sizes from &string starting at &offset.
	"""
	current = offset

	for size in sizes:
		end = current + size
		yield string[current:end]

		current = end + 1

def _unpack(transport, line:str, offset:int, limit:int, context=None,
		_enter_fields_len=len(_tty_field_lengths),
		_exit_fields_len=len(_tty_exit_fields),
		_enter_data_len=len(_tty_data_extension),
		_exit_extension_len=len(_tty_exit_extension),
		_ext_offset=-(len(_tty_exit_extension)+2),
		_ext_indicator=_tty_exit_extension,
		_create_message=types.Message.from_arguments_v1,
		_create_estruct=types.EStruct.from_fields_v1,
		_get_type_symbol=type_codes.get,
	) -> Envelope:
	"""
	# Unpack a serialized status frame.
	"""

	assert line[offset+2] == ' ' # [XX ...]
	if line[-1:] == '\n':
		_ext_offset -= 1
	if line[-3:-2] != ')':
		# No channel.
		_ext_offset += 1

	idstr = line[offset:offset+2]
	offset += 3
	code = type_integer_code(idstr)

	data = None
	channel = None
	loadsignal = None

	sof = offset + _enter_fields_len

	# Extract structured fields.
	if line[_ext_offset:_ext_offset+_exit_extension_len] == _ext_indicator:
		# Structured.
		end_fs = line.find(_tty_exit_fields, sof)
		assert end_fs != -1 # Malformed Length Area

		lengths = list(map(int, line[sof:end_fs].strip().split()))

		sofd = end_fs + _exit_fields_len
		*fields, channel_area, ext_data = list(_select_fields(line, end_fs + _exit_fields_len, lengths))

		try:
			channel, loadsignal = channel_area.split(":", 1)
			channel = channel.strip('()')
		except:
			channel = None
			if ext_data:
				loadsignal = channel_area
			else:
				channel = channel_area.strip("\x1b;0123456789-mx[]()")
	else:
		# Unstructured.
		ext_data = None
		fields = line[offset:limit].split(' ')
		last = fields[-1]

		if not last:
			del fields[-1]
		elif last[0] == "(" and last[-1] == ")":
			try:
				channel, loadsignal = last.split(":", 1)
			except:
				channel = last
				loadsignal = None

			channel = channel.strip('()')
			del fields[-1]
		else:
			pass

	# Clean the load signal of the SGR codes.
	if loadsignal is not None:
		loadsignal = loadsignal.strip("\x1b;0123456789-mx[]()")
		if loadsignal == "+":
			data = transport(ext_data) # unpack
		else:
			# Usually reference.
			data = ext_data
	else:
		data = None

	msg = _create_message(
		context,
		_create_estruct(
			protocol=protocol,
			identifier=idstr,
			code=code,
			symbol=_get_type_symbol(idstr, 'unrecognized'),
			abstract=' '.join(fields)
		),
		data=data
	)
	msg.msg_parameters['envelope-fields'] = fields

	return (channel or None, msg)

def unpack(
		transport:typing.Callable[[str], types.Roots],
		line:str,
		context:types.Trace=None
	) -> Envelope:
	"""
	# Extract a status frames &types.Message from the serialized &line.
	# Returns a tuple whose first item is the envelope's channel and the second
	# is the &types.Roots instance.

	# [ Parameters ]

	# /transport/
		# Function used to extract the data extension of the frame.
	# /line/
		# A single serialized line.
	# /context/
		# Optional &types.Trace instance to use as the returned Message's context.
	"""
	return _unpack(transport, line, 1, len(line)-2, context=context)

def default_data_transport() -> typing.Tuple[typing.Callable, typing.Callable]:
	"""
	# Create the default transport composition supporting frame data extension I/O.
	"""
	# status.types.* <-> objects.Transport <-> JSON <-> DEFLATE <-> base64 <-> Rendered Frame
	import json
	import base64
	import zlib
	from . import objects

	objtransport = objects.allocate()

	def _frame_pack_data(message:object,
			b64e=base64.b64encode,
			deflate=zlib.compress,
			serial=json.dumps,
			prepare=objtransport.prepare
		) -> bytes:
		return b64e(deflate(serial(prepare(message)).encode('utf-8')))

	def _frame_unpack_data(data:str,
			b64d=base64.b64decode,
			inflate=zlib.decompress,
			structure=json.loads,
			interpret=objtransport.interpret
		) -> object:
		return interpret(structure(inflate(b64d(data))))

	return _frame_unpack_data, _frame_pack_data

def stdio() -> typing.Tuple[typing.Callable, typing.Callable]:
	"""
	# Construct message I/O functions for parsing and serializing Status Frames.

	# The returned pair should be cached for repeat use.
	"""
	i, o = default_data_transport()
	return (functools.partial(unpack, i), functools.partial(pack, o))

def declaration(data=None, format='base64', compression='deflate', Message=types.Message):
	"""
	# Construct a custom protocol declaration message.
	"""
	return Message.from_arguments_v1(
		None,
		types.EStruct.from_fields_v1(
			protocol=protocol,
			symbol="protocol-message",
			abstract="PROTOCOL: tty-notation-1",
			identifier="!?",
			code=type_integer_code("!?"),
		),
		**{
			'envelope-fields': [
				'PROTOCOL:', protocol,
				'tty-notation-1',
				'/'.join((format, compression)),
			],
			'data': data,
		},
	)

# Structured protocol declaration.
tty_notation_1_message = declaration()

# Serialized protocol declaration.
tty_notation_1_string = "[!? " + tty_notation_1_message.msg_event.abstract + "]\n"

def message_qualification(fields:typing.Sequence[str]):
	"""
	# Returns the first item in &fields if the string ends with a colon.
	# &None otherwise.
	"""

	if fields[0][-1] == ':':
		return fields[0]

	return None

def message_subject_field(fields:typing.Sequence[str]):
	"""
	# Returns the first item in &fields if the string is surrounded with parenthesis.
	# &None otherwise.
	"""

	if fields[0][0] == "(" and fields[0][-1] == ")":
		return fields[0]

	return None

def message_directed_areas(fields:typing.Sequence[str], start, end, arrows={'<-', '<->', '->'}):
	"""
	# Return the slices marking the areas before and after the first item
	# contained in &arrows.

	# &None if no items in &fields are contained in &arrows.
	"""

	for i in range(start, end):
		f = fields[i]
		if f in arrows:
			return (f, slice(start, i), slice(i+1, end))

	return None
