"""
Low-level Hypertext Transfer Protocol tools.

Provides protocol tokenization, field parsers, and protocol serialization for
implementing a server or a client.
"""
import itertools
import functools
from .data import http

# Raw binary header indicating chunking should be used.
CHUNKED_TRANSFER = b'Transfer-Encoding: chunked' + http.CRLF

class Event(int):
	"""
	An HTTP event; essentially an enumeration, but kept as an integer subclass for
	backwards compatibility.

	Event Structure:

	/(identifier)`BYPASS`
		(&Event.bypass, &bytes)

	/(identifier)`RLINE`
		For requests: (&Event.rline, (method, uri, version))
		For responses: (&Event.rline, (version, response_code, description))

	/(identifier)`CHUNK`
		(&Event.chunk, &bytearray)

	/(identifier)`CONTENT`
		(&Event.content, &bytearray)

	/(identifier)`HEADERS`
		(&Event.headers, [(&bytes, &bytes),...])

	/(identifier)`TRAILERS`
		(&Event.trailers, [(&bytes, &bytes),...])

	/(identifier)`MESSAGE`
		(&Event.message, &None)

	/(identifier)`VIOLATION`
		(&Event.trailers, (type, ...))

		Where `type` is:

		/`'limit'`
			A configured limit was exceeded.

		/`'protocol'`
			A protocol error occurred.
	"""

	__slots__ = ()

	names = (
		'RLINE',
		'HEADERS',
		'CONTENT',
		'CHUNK',
		'TRAILERS',
		'MESSAGE',
		'VIOLATION',
		'BYPASS', # for indexing; names[Event.bypass==-1] == 'BYPASS'
	)

	codes = {
		'RLINE': 0,
		'HEADERS': 1, # Terminated by a HEADERS event with an empty sequence.
		'CONTENT': 2,
		'CHUNK': 3,
		'TRAILERS': 4,
		'MESSAGE': 5, # EOM: End of Message
		'VIOLATION': 6,
		'BYPASS': -1,
	}

	def __repr__(self, format = "{0}.{1}.{2}".format, names = names):
		return format(__name__, self.__class__.__name__, names[self].lower())

	def __str__(self):
		return self.names[self]

Event.bypass = Event(Event.codes['BYPASS'])
Event.rline = Event(Event.codes['RLINE'])
Event.headers = Event(Event.codes['HEADERS'])
Event.content = Event(Event.codes['CONTENT'])
Event.chunk = Event(Event.codes['CHUNK'])
Event.trailers = Event(Event.codes['TRAILERS'])
Event.message = Event(Event.codes['MESSAGE'])
Event.violation = Event(Event.codes['VIOLATION'])

EOH = (Event.headers, ())
EOM = (Event.message, None)

###
# Field extraction and transfer length handling.
##
# http://www.faqs.org/rfcs/rfc2616.html
# Some notably relevant portions are:
#  4.4 Message Length (chunked vs Content-Length)
def Tokenization(
		max_line_size : int = 0xFFFF*3, # maximum length of the Request-Line or Response-Line
		max_headers : int = 1024, # maximum number of headers to accept
		max_trailers : int = 32, # maximum number of trailers to accept
		max_header_size : int = 0xFFFF*2, # len(field-name) + len(field-value)
		max_trailer_size : int = 0xFFFF*2, # len(field-name) + len(field-value)
		max_chunk_line_size : int = 0xFFF, # chunk size portion, not the chunk data size

		# local()-izations
		len = len, tuple = tuple,
		bytes = bytes, int = int,
		bytearray = bytearray,
		bstrip = bytes.strip,
		bastrip = bytearray.strip,
		map = map, range = range,
		max = max,

		CRLF = http.CRLF, SP = http.SP,
		PROTOCOLS = http.VERSIONS,

		NO_BODY_RESPONSE_CODES = frozenset((
			http.codes['NOT_MODIFIED'], http.codes['NO_CONTENT']
		)),

		SIZE_DESIGNATION = frozenset((
			b'content-length', b'transfer-encoding',
		)),

		bypass_ev = Event.bypass,
		rline_ev = Event.rline,
		headers_ev = Event.headers,
		content_ev = Event.content,
		chunk_ev = Event.chunk,
		trailers_ev = Event.trailers,
		violation_ev = Event.violation,
	):
	"""
	An HTTP 1.0 and 1.1 message parser. Emits HTTP events from the given binary data.

	#!/matrix
		One of: (Method, Request-URI, HTTP-Version) | (HTTP-Version, Status-Code, Reason-Phrase)
		Zero or more of: [(field-name, field-value), ...]
		One of: ()
		Zero or more of: message-body-byte-parts
		One of: None # body terminator
		Zero or more of: [(field-name, field-value), ...] # Trailers
		One of: ()

	The generator is configured to loop perpetually in order to handle pipelined
	requests.

	The contents of the above are all bytes() objects. No decoding is performed.

	In addition to giving structure to HTTP line and headers, it will handle the
	transfer encoding of the message's body. (*Not* at the entity level.)
	"""

	# Parse Request and Headers
	message_number = -1
	events = []
	fnf = -1

	req = bytearray()
	find = req.find
	extend = req.extend

	# initial next(g)
	extend((yield None))
	body_size = 0

	while True:
		body_ev = content_ev # in chunking cases, this get turned into chunk_ev
		has_body = True
		# Content-Length/is chunking
		size = None

		if events and not req:
			# flush EOM event
			extend((yield events))
			events = []

		# Read initial request/response line.
		eof = fnf
		pos = 0
		line = None
		while line is None:
			eof = find(CRLF, pos, max_line_size)
			if eof == -1:

				if max_line_size is not None and len(req) > max_line_size:
					events.append((
						violation_ev, ('limit', 'max_line_size', max_line_size)
					))
					events.append((bypass_ev, req))

					del find
					req = (yield events)
					while True:
						req = (yield [(bypass_ev, req)])

				# Need more data to complete the initial line.
				pos = max(len(req) - 1, 0)
				extend((yield events))
				events = []
			elif eof == 0:
				# strip a preceding CRLF
				del req[0:2]
				eof = fnf
			else:
				# found it
				line = bytes(req[:eof])
				del req[:eof + 2]
		line = tuple(line.split(SP, 2))
		events.append((rline_ev, line))

		# Override the possibility of a body.
		# Methods must not contain slashes, but HTTP-Versions do.
		if has_body is True and b'/' in line[0]:
			# certain responses do not have bodies,
			# toggle has_body to False in these cases.
			if line[1] in NO_BODY_RESPONSE_CODES:
				# rfc 10.2.5 204 No Content
				# rfc 10.3.5 304 Not Modified
				has_body = False

		# Emit headers.
		pos = 0
		nheaders = 0
		chunk_size = None
		headers = []
		add_header = headers.append
		connection = None

		startswith = req.startswith
		while not startswith(CRLF):
			eof = find(CRLF, pos, max_header_size)
			if eof == -1:
				# no terminator, need more data
				##
				# update position to the end of the buffer
				if headers:
					events.append((headers_ev, headers))
					headers = []
					add_header = headers.append
				reqlen = len(req)
				pos = max(reqlen - 1, 0)

				if max_header_size is not None and reqlen > max_header_size:
					events.append((
						violation_ev,
						('limit', 'max_header_size', max_header_size)
					))
					events.append((bypass_ev, req))

					del find
					del startswith
					req = (yield events)
					del events
					while True:
						req = (yield [(bypass_ev, req)])

				extend((yield events))
				events = []
				# continues; no double CRLF yet.
			elif eof:
				# EOF must be > 0, otherwise it's the end of the headers.
				# Got a header within the constraints (max_header_size).

				# Spell out header tuple constructor for performance.
				eoi = find(b':', 0, eof) # Use find rather than split to avoid list().
				header = (bstrip(bytes(req[:eoi])), bstrip(bytes(req[eoi+1:eof])))
				del req[:eof+2]

				field_name = header[0].lower()

				# Identify message size.
				if field_name == b'connection':
					# need to know this in order to handle responses without content-length
					connection = header[1]
				elif has_body is True and field_name in SIZE_DESIGNATION:
					if size is not None:
						# Size was already set; likely violation.
						pass
					elif field_name == b'content-length':
						try:
							size = int(header[1])
						except ValueError:
							# Do NOT include the bogus Content-Length;
							if headers:
								events.append((headers_ev, headers))
							del headers
							events.append((
								violation_ev,
								('protocol', 'Content-Length', header[1])
							))
							events.append((bypass_ev, req))

							del find
							del startswith
							del add_header
							req = (yield events)
							while True:
								req = (yield [(bypass_ev, req)])

					elif field_name == b'transfer-encoding' and header[1].lower() == b'chunked':
						# It's chunked. See section 4.4 of the protocol.
						chunk_size = -1
						size = -1
						body_ev = chunk_ev

				add_header(header)
				nheaders += 1
				pos = 0
				if max_headers is not None and nheaders > max_headers:
					events.append((headers_ev, headers))
					events.append((
						violation_ev,
						('limit', 'max_headers', nheaders, max_headers)
					))
					events.append((bypass_ev, req))

					del find
					del startswith
					del headers
					del add_header
					req = (yield events)
					while True:
						req = (yield [(bypass_ev, req)])

		# Emit remaining headers.
		if headers:
			events.append((headers_ev, headers))

		# Avoid holding old references in case of future subsitution.
		del headers
		del add_header
		del startswith

		# Terminator
		events.append(EOH)

		# headers processed, redetermine has_body given &size.
		if has_body is True and size is None:
			# size was not initialized so it should assume there's no body
			has_body = False

		# Trim trailing CRLF.
		del req[:2]
		pos = 0

		# End of headers; emit body, if any.
		while size:
			while chunk_size == -1:
				##
				# Transfer-Encoding: chunked; read the chunk size line
				eof = find(CRLF, pos, max_chunk_line_size)
				if eof == -1:
					# no terminator, need more data

					# make sure we are not exceeding the max chunk line size
					if max_chunk_line_size is not None and len(req) > max_chunk_line_size:
						events.append((
							violation_ev,
							('limit', 'max_chunk_line_size', len(req), max_chunk_line_size)
						))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

					# Update position to the end of buffer minus one so it's not
					# scanning for CRLF through data that it has already scanned.
					pos = max(len(req) - 1, 0)
					extend((yield events))
					events = []
					# continues
				else:
					# found CRLF of chunk size line
					pos = 0
					# new chunk
					extsep = find(b';', 0, eof)
					if extsep == -1:
						extsep = eof
					else:
						# XXX: Ignoring chunk extensions..
						chunk_extensions = req[extsep:eof]
					chunk_field = req[:extsep]
					del req[0:eof+2]

					try:
						chunk_size = int(chunk_field, 16)
					except ValueError:
						events.append((violation_ev, ('protocol', 'chunk-field', chunk_field)))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

					del chunk_field
					size = chunk_size

			# Transfer known size.
			n = len(req)
			if n < size:
				# Consume &size bytes emitting body events.
				size = size - n
				body_size += len(req)
				events.append((body_ev, req))

				# Replace req entirely with input.
				# Loop only needs the size to progress,
				# so del find to get rid of the reference to req.
				del find
				req = (yield events)

				# Act nearly as a passthrough here when the size is known.
				n = len(req)
				while n < size:
					# len(req) < size == True
					size = size - n
					body_size += len(req)
					events = ((body_ev, req),)
					# get new data; all of req emitted prior
					# so complete replacement here.
					req = (yield events)
					n = len(req)
				else:
					# req exceeded the remaining size, so its on the edge
					events = []

					# Make sure it's a bytearray, and update find()
					req = bytearray(req)
					find = req.find
					extend = req.extend

			# &req is now larger than the remaining &size.
			# There is enough data to complete the body or chunk.

			if size:
				body_size += size
				events.append((body_ev, req[0:size]))
				del req[0:size]
				size = 0

			assert size == 0 # Done with body or chunk *data*.

			# If chunking, expect a CRLF
			# and continue reading chunks iff chunk_size.
			if chunk_size is not None:
				if chunk_size == 0:
					# Final chunk; don't assume there's
					# a CRLF as there would be for normal chunks.
					break

				# Process CRLF on each chunk end.
				while not req.startswith(CRLF):
					# continue until we get a CRLF
					if len(req) > 2:
						# req has content but it's not a CRLF? bad
						events.append((
							violation_ev,
							('protocol', 'bad-chunk-terminator', req[:2])
						))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

					extend((yield events))
					events = []

				assert req[0:2] == CRLF

				del req[0:2]
				# end of chunks?
				if chunk_size != 0:
					# more chunks coming
					chunk_size = -1
					size = -1
				# else assert chunk_size == size == 0

		# :while size
		else:
			if size is None and connection == b'close':
				# no identified size and connection is close
				del find
				events.append(EOM)
				while True:
					# Everything is bypass after this point.
					# The connection is closed and there's no body.
					if req:
						events.append((bypass_ev, req))
					req = (yield events)
					events = []

		# Body termination indicator; but there may be trailers to parse.
		if has_body:
			# Used to signal the stream of EOF;
			# primarily useful to signal compression
			# transformations to flush the buffers.
			events.append((body_ev, b''))

		if chunk_size == 0:
			# Chunking occurred, read and emit trailers.
			# Trailers are supposed to be declared ahead of time,
			# so it may be reasonable to thrown a violation.
			ntrailers = 0
			trailers = []
			eof = find(CRLF, 0, max_header_size)
			while eof != 0:
				if eof == -1:
					# No terminator, need more data.
					if trailers:
						events.append((trailers_ev, trailers))
						trailers = []
					if max_trailer_size is not None and len(req) > max_trailer_size:
						events.append((
							violation_ev, ('limit', 'max_trailer_size', len(req))
						))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

					extend((yield events))
					events = []
					# look for eof again
				elif eof:
					# found the terminator
					ntrailers += 1
					trailer = tuple(map(bytes, map(bastrip, req[:eof].split(b':', 1))))
					del req[0:eof+2]
					trailers.append(trailer)

					if max_trailer_size is not None and eof > max_trailer_size:
						# Limit Violation
						events.append((trailers_ev, trailers))
						del trailers
						events.append((
							violation_ev, ('limit', 'max_trailer_size', eof)
						))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

					if max_trailers is not None and ntrailers > max_trailers:
						# Limit Violation
						events.append((trailers_ev, trailers))
						del trailers
						events.append((
							violation_ev, ('limit', 'max_trailers', ntrailers)
						))
						events.append((bypass_ev, req))

						del find
						req = (yield events)
						del events
						while True:
							req = (yield [(bypass_ev, req)])

				# find next end of field.
				eof = find(CRLF, 0, max_header_size)

			# remove the trailing CRLF
			del req[0:2]
			# Emit remaining headers.
			if trailers:
				events.append((trailers_ev, trailers))
			# signals the end of trailers
			trailers = ()
			events.append((trailers_ev, trailers))
		# chunk_size == 0

		# finish up by resetting size and emitting EOM on continuation
		size = None
		events.append(EOM)
	else: # for message_number in range(...):
		# too many messages
		events.append((violation_ev, ('limit', 'max_messages', max_messages)))
		del find
		while True:
			events.append((bypass_ev, req))
			req = (yield events)
			events = []
Disassembler = Tokenization

def disassembly(**config):
	"""
	Returns an already started &Disassembler generator.
	"""
	global Disassembler
	d = Disassembler(**config)
	d.__next__()
	return d

def headers(headers, chain = itertools.chain.from_iterable, CRLF = http.CRLF, HFS = http.HFS):
	return chain(((x[0], HFS, x[1], CRLF) for x in headers))

@functools.lru_cache(16)
def chunk_size(length, CRLF=http.CRLF, hex=hex):
	return hex(length).encode('ascii')[2:] + CRLF

def chunk(data, len=len, CRLF=http.CRLF):
	"""
	Returns a tuple of (chunk-size + CRLF, chunk-data, CRLF).

	Joining data into a single buffer is avoided for the express
	purpose of allowing the data buffer to be passed through.
	In cases where a shared memory segment is referenced, this
	can be critical for proper performance.

	#!/pl/python
		assert chunk(b'data') == (b'4\\r\\n', b'data', b'\\r\\n')
	"""
	global chunk_size
	return (chunk_size(len(data)), data, CRLF)

trailers = headers

def Serialization(
		SP = http.SP, CRLF = http.CRLF,
		HFS = http.HFS,
		trailers_ev = Event.trailers,
		headers_ev = Event.headers,
		rline_ev = Event.rline,
		content_ev = Event.content,
		chunk_map = {Event.chunk: chunk, Event.content: lambda x: (x,)}
	):
	"""
	Assemble HTTP events back into a sequences of bytes.
	"""

	events = (yield None)
	while True:
		buf = []
		append = buf.append

		for x in events:
			if x[0] == rline_ev:
				append(SP.join(x[1]))
				append(CRLF)
			elif x[0] in {trailers_ev, headers_ev}:
				if not x[1]:
					# end of headers
					append(CRLF)
				else:
					append(CRLF.join([y[0] + HFS + y[1] for y in x[1]]))
					append(CRLF)
			elif x == EOM:
				pass
			else:
				# Default to concatenation of event payload
				buf.extend(chunk_map[x[0]](x[1]))

		events = (yield buf)
Assembler = Serialization

def assembly(**config):
	"""
	Return a started &Assembler generator.
	"""
	global Assembler
	g = Assembler()
	g.__next__()
	return g
