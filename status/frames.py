"""
# Formatting and parsing tools for status frame transport envelopes.

# This module provides conceptual definitions for Status Frame events (&types.EStruct) and
# I/O operations supporting the transmission of those events.

# Status Frames are &types.Frame instances that can be serialized into and parsed from a
# data stream.

# [ Usage ]

# The operation used to serialize and load the data extension is decoupled, so an allocation
# function is provided to apply the defaults for the data extension transport:
# #!syntax/python
	from fault.status import frames

# Frame envelopes may or may not have content (data extensions):
# #!syntax/python
	msg = compose('!#', "ERROR: no such resource")
	sys.stdout.write(frames.sequence(msg))

	"[!# ERROR: no such resource]\n"

# Serialized messages are expected to include the trailing newline:
# #!syntax/python
	for line in sys.stdin.readlines():
		msg = frames.structure(line)

# [ Properties ]

# /protocol/
	# String identifying the status frames (event) protocol.
"""
import typing
import functools
import base64

from . import transport
from . import types

protocol = 'http://fault.io/protocol/status/frames'
ttyn_data_url = b'data:text/plain;charset=utf-8;base64,'

def compose(ftype:str, synopsis:str,
		channel:str=None, extension=None,
		Class=types.Frame, Event=types.EStruct.from_fields_v1,
	) -> types.Frame:
	"""
	# Create a status frame using the envelope's symbol and synopsis.
	"""
	eid = type_codes[ftype] #* Recognize identifier.
	ev = Event(protocol, eid, synopsis, ftype, type_integer_code(ftype))
	return Class((channel, ev, extension))

def _frame_pack_extension(data,
		b64e=base64.b64encode,
		sequence=transport.sequence,
	) -> bytes:
	return ttyn_data_url + b64e(sequence(data).encode('utf-8'))

def _frame_unpack_extension(data:str,
		b64d=base64.b64decode,
		structure=transport.structure,
	) -> object:
	url_type, ext = data.split(';base64,', 1)
	return structure(b64d(ext).decode('utf-8'))

# Protocol identity for &types.Frame instances.
protocol = "http://fault.io/protocol/status/frames"

# Two-Character EStruct.identifier.
type_codes = {
	# [!? PROTOCOL: http://fault.io/protocol/status/frames tty-notation-1]
	"!?": 'message-protocol',
	"!&": 'reference',

	# Abstract Transaction progress.
	"><": 'transaction-failed',
	"<>": 'transaction-executed',
	"->": 'transaction-started',
	"--": 'transaction-event',
	"<-": 'transaction-stopped',

	# Warnings, Errors, and Information with respect to some conceptual level of a frame source.
	"!#": 'message-application',
	"!*": 'message-framework',
	"!~": 'message-trace',

	# Messages sent by user entities.
	"!%": 'message-administrative',
	"!>": 'message-entity',

	# Resource Content Manipulations
	"+=": 'elements-inserted', # Added
	"-=": 'elements-deleted', # Removed
	"Δ=": 'elements-delta', # Compound Change
	"<=": 'elements-reverted',
	"==": 'elements-committed',

	# Resource Container Manipulations
	"+.": 'resource-initialized',
	"-.": 'resource-deleted',
	"±.": 'resource-relocated',
	"*.": 'resource-replicated',
	"&.": 'resource-referenced',
	"=.": 'resource-rewritten',
	"Δ.": 'resource-delta', # Property/metadata changes.

	# Archive I/O
	"^*": 'archive-extraction-replicated',
	"^+": 'archive-extraction-replicated-merge',

	"√*": 'archive-delta-replicated-into',
	"√+": 'archive-delta-merged-into',
	"√-": 'archive-delta-deleted',
	"√&": 'archive-delta-referenced',

	# Transfer Snapshots.
	"↑.": 'resource-transmitted',
	"↓.": 'resource-received',

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

# OSC declaring a frame placed before the closing ")]" or "]".
# The inconsistent placement is intended to avoid surprises when
# attempting to match strings with frame boundaries.
_ttyn_signature = "\x1b]\x03\x1b\\"

# Escapes to pack a "data:" link on the extension size with coloring.
_ttyn_open_url = "\x1b[34;2m" "\x1b]8;;"
_ttyn_close_url = "\x1b\\"
_ttyn_reset_url = "\x1b]8;;" "\x1b\\" "\x1b[39;22m"

_frame_open = "[{ts} "
_frame_exit = "]\n"
_loaded_frame_start = _frame_open + "{image}"
_loaded_frame_partition = " ({channel}{open}"
_loaded_frame_stop = "{finish}{signal}{size}{close}" + _ttyn_signature + ")]\n"
_empty_frame_stop = _ttyn_signature + "]\n"

def _pack(
		frame:types.Frame, channel=None,
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

	if channel is None:
		channel = frame.f_channel or ''
	ext = frame.f_extension
	ts = frame.f_event.identifier
	image = frame.f_image

	if ext or channel:
		if ext is None:
			signal = ""
			load = b""
			size = ""
		else:
			load = _frame_pack_extension(ext.items())
			signal = "+"
			size = str(len(load))

		start = _fmt_lframe_start(ts=ts, image=image) + _fmt_lframe_part(
			channel=channel,
			open=_ttyn_open_url,
		)
		end = _fmt_lframe_stop(
			signal=signal,
			size=size,
			finish=_ttyn_close_url,
			close=_ttyn_reset_url,
		)
	else:
		# Neither extension or channel.
		load = b""
		start = _fmt_lframe_start(ts=ts, image=image)

		if image.endswith(')'):
			# Escape close.
			end = _fmt_eframe_stop()
		else:
			end = _frame_exit

	return (start, load, end)

def sequence(frame:types.Frame, channel=None) -> str:
	"""
	# Pack a status frame into a &str for transmission.

	# Constructs a single &str instance.

	# [ Parameters ]

	# /frame/
		# The status frame to be represented in serial form.
	"""
	s1, s2, s3 = _pack(frame, channel=channel)
	return s1 + s2.decode('ascii') + s3

def _unpack(line:str, offset:int, limit:int,
		_frame_indicator=_ttyn_signature,
		_indicator_offset=-(len(_ttyn_signature)+2),
		_indicator_length=len(_ttyn_signature),
		_create_message=types.Frame,
		_create_estruct=types.EStruct.from_fields_v1,
		_get_type_symbol=type_codes.get,
	) -> types.Frame:
	"""
	# Unpack a serialized status frame.
	"""

	if line[-1:] == '\n':
		_indicator_offset -= 1
	if line[-3:-2] != ')':
		# No channel or extension.
		_indicator_offset += 1

	typarea = line.find(' ', offset)
	idstr = line[offset:typarea]
	offset = typarea + 1
	code = type_integer_code(idstr)

	data = None
	channel = None
	loadsignal = None

	# Extract structured fields.
	if line[_indicator_offset:_indicator_offset+_indicator_length] == _frame_indicator:
		try:
			prefix, ext_data, tail = line.rsplit('\x1b]8;;', 2)
		except ValueError:
			ext_data = ''
			prefix = line
		else:
			# Trim the data extension exit.
			ext_data = ext_data[:ext_data.find(_ttyn_close_url)]

		try:
			image, channel_area = prefix.rsplit('(', 1)
		except ValueError:
			image = prefix
			channel_area = ''

		image = image[offset:]

		try:
			channel, loadsignal = channel_area.split('\x1b', 1)
			channel = channel.strip('()')
		except:
			if ext_data:
				loadsignal = channel_area
			else:
				channel = channel_area.strip("\x1b;0123456789-mx[]()")
	else:
		# Unstructured.
		ext_data = None
		if line[-3:-1] == ')]':
			soc = line.rfind('(')
			image = line[offset:soc]
			channel = line[soc+1:-3]
			loadsignal = None
		else:
			image = line[offset:-2]
			loadsignal = None

	# Clean the load signal of the SGR codes.
	if ext_data:
		loadsignal = loadsignal.strip("\x1b;0123456789-mx[]()")
		data = dict(_frame_unpack_extension(ext_data))
	else:
		data = None

	return types.Frame((
		channel or None,
		_create_estruct(
			protocol=protocol,
			identifier=idstr,
			code=code,
			symbol=_get_type_symbol(idstr, 'unrecognized'),
			abstract=image.strip()
		),
		data,
	))

def structure(line:str) -> types.Frame:
	"""
	# Extract a status frame, &types.Frame, from the given &line.

	# [ Parameters ]

	# /line/
		# A single serialized line.
	"""
	return _unpack(line, 1, len(line)-2)

def declaration(channel=None, extension=None, Frame=types.Frame):
	"""
	# Construct a custom protocol declaration message.
	"""
	return types.Frame((
		channel,
		types.EStruct.from_fields_v1(
			protocol=protocol,
			symbol="protocol-message",
			abstract=' '.join([
				'PROTOCOL:', protocol,
				'tty-notation-1',
			]),
			identifier="!?",
			code=type_integer_code("!?"),
		),
		extension,
	))

# Structured protocol declaration.
tty_notation_1_message = declaration()

# Serialized protocol declaration.
tty_notation_1_string = "[!? " + tty_notation_1_message.f_event.abstract + "]\n"

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
