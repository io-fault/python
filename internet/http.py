"""
# Low-level Hypertext Transfer Protocol tools.

# Provides protocol tokenization, field parsers, and protocol serialization for
# implementing a server or a client.

# [ Events ]

# /(identifier)`BYPASS`/
	# (&ev_bypass, &bytes)

# /(identifier)`RLINE`/
	# For requests: (&ev_rline, (method, uri, version))
	# For responses: (&ev_rline, (version, response_code, description))

# /(identifier)`CHUNK`/
	# (&ev_chunk, &bytearray)

# /(identifier)`CONTENT`/
	# (&ev_content, &bytearray)

# /(identifier)`HEADERS`/
	# (&ev_headers, [(&bytes, &bytes),...])

# /(identifier)`TRAILERS`/
	# (&ev_trailers, [(&bytes, &bytes),...])

# /(identifier)`MESSAGE`/
	# (&ev_message, &None)
	# End of message.

# /(identifier)`VIOLATION`/
	# (&ev_trailers, (type, identifier, message, context))

	# Where `type` is:

	# /`'limit'`/
		# A configured limit was exceeded.

	# /`'protocol'`/
		# A protocol error occurred.

# /(identifier)`WARNING`/
	# (&ev_warning, (type, identifier, message, context))
"""
import itertools
import functools
from .data import http as protocoldata

ev_bypass = -2
ev_violation = -1
ev_rline = 0
ev_headers = 1
ev_content = 2
ev_chunk = 3
ev_trailers = 4
ev_message = 5 # end of message
ev_warning = 6

event_symbols = {
	ev_bypass: 'bypass',
	ev_violation: 'violation',
	ev_rline: 'rline',
	ev_headers: 'headers',
	ev_content: 'content',
	ev_chunk: 'chunk',
	ev_trailers: 'trailers',
	ev_message: 'message',
	ev_warning: 'warning',
}

EOH = (ev_headers, ())
EOM = (ev_message, None)

###
# Field extraction and transfer length handling.
##
# https://tools.ietf.org/html/rfc7230#section-3.3.3
def Tokenization(
		disposition:str='server',
		max_line_size : int = 4096, # maximum length of the Request-Line or Response-Line
		max_headers : int = 1024, # maximum number of headers to accept
		max_trailers : int = 32, # maximum number of trailers to accept
		max_header_size : int = 0xFFFF*2, # len(field-name) + len(field-value)
		max_header_set_size : int = 1024*4*2, # maximum size to scan for EOH
		max_trailer_size : int = 0xFFFF*2, # len(field-name) + len(field-value)
		max_chunk_line_size : int = 1024, # chunk size portion, not the chunk data size

		# local()-izations
		len = len, tuple = tuple,
		bytes = bytes, int = int,
		bytearray = bytearray,
		bstrip = bytes.strip,
		bastrip = bytearray.strip,
		map = map, range = range,
		max = max,

		CRLF = protocoldata.CRLF, SP = protocoldata.SP,
		PROTOCOLS = protocoldata.VERSIONS,

		bypass_ev = ev_bypass,
		rline_ev = ev_rline,
		headers_ev = ev_headers,
		content_ev = ev_content,
		chunk_ev = ev_chunk,
		trailers_ev = ev_trailers,
		violation_ev = ev_violation,
		warning_ev = ev_warning,
	):
	"""
	# An HTTP 1.0 and 1.1 message parser. Emits HTTP events from the given binary data.

	#!/matrix
		# One of: (Method, Request-URI, HTTP-Version) | (HTTP-Version, Status-Code, Reason-Phrase)
		# Zero or more of: [(field-name, field-value), ...]
		# One of: ()
		# Zero or more of: message-body-byte-parts
		# One of: None # body terminator
		# Zero or more of: [(field-name, field-value), ...] # Trailers
		# One of: ()

	# The generator is configured to loop perpetually in order to handle pipelined
	# requests.

	# The contents of the above are all bytes() objects. No decoding is performed.

	# In addition to giving structure to HTTP line and headers, it will handle the
	# transfer encoding of the message's body. (*Not* at the entity level.)

	# [ Engineering ]

	# Currently, this does not properly manage the Transfer-Encoding header in
	# if the client where to submit a TE header.
	# This implementation only looks for a single chunked entry where a stack
	# of applied encodings may be present.
	"""

	# Parse Request and Headers
	is_client = disposition == 'client'
	message_number = -1
	events = []
	addev = events.append
	fnf = -1

	req = bytearray()
	buflen = req.__len__
	find = req.find
	extend = req.extend
	startswith = req.startswith

	# initial next(g)
	extend((yield None))
	body_size = 0

	while True:
		keep_alive = None # Unspecified keep-alive
		cl = []
		te = []
		cn = []
		ctl_headers = {
			b'content-length': cl,
			b'transfer-encoding': te,
			b'connection': cn,
		}
		body_ev = content_ev # in chunking cases, this get turned into chunk_ev
		has_body = True
		# Content-Length/is chunking
		size = None

		if events and not req:
			# flush EOM event
			extend((yield events))
			events = []
			addev = events.append

		# Read initial request/response line.
		eof = fnf
		pos = 0
		line = None
		while line is None:
			eof = find(b"\r\n", pos, max_line_size)
			if eof == -1:

				if buflen() > max_line_size:
					addev((
						violation_ev, ('limit', 'max_line_size', max_line_size)
					))
					addev((bypass_ev, req))

					del find, extend, buflen, startswith
					req = (yield events)
					del events, addev
					while True:
						req = (yield [(bypass_ev, req)])

				# Need more data to complete the initial line.
				pos = max(buflen() - 1, 0)
				extend((yield events))
				events = []
				addev = events.append
			elif eof == 0:
				# strip a preceding CRLF
				del req[0:2]
				eof = fnf
			else:
				# found it
				line = bytes(req[:eof])
				del req[:eof + 2]
		line = tuple(line.split(b" ", 2))
		addev((rline_ev, line))

		# Methods do not contain slashes, but HTTP-Versions do.
		if is_client and (line[1] in {b'204', b'304'} or line[1][:1] == b'1'):
			# 1xx
			# rfc 10.2.5 204 No Content
			# rfc 10.3.5 304 Not Modified
			has_body = False

		# Emit headers.
		chunk_size = None

		eoh = find(b"\r\n\r\n", 0, max_header_set_size)
		if eoh != -1:
			# Fast path when full headers are present.
			header = None
			headers = bytes(req[:eoh]).split(b"\r\n")
			nheaders = len(headers)

			for i in range(nheaders):
				header = headers[i].split(b":")
				header = headers[i] = (bstrip(header[0]), bstrip(header[1]))

				field = header[0].lower()
				if field in ctl_headers:
					ctl_headers[field].extend(x.strip() for x in header[1].split(b','))

			del req[:eoh+4]
			# Terminator
			addev((headers_ev, headers))
			addev(EOH)
			del headers, header
		else:
			pos = 0
			nheaders = 0
			headers = []
			add_header = headers.append

			startswith = req.startswith
			while not startswith(b"\r\n"):
				eof = find(b"\r\n", pos, max_header_size)
				if eof == -1:
					# no terminator, need more data
					##
					# update position to the end of the buffer
					if headers:
						addev((headers_ev, headers))
						headers = []
						add_header = headers.append
					reqlen = buflen()
					pos = max(reqlen - 1, 0)

					if reqlen > max_header_size:
						addev((
							violation_ev,
							('limit', 'max_header_size', max_header_size)
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith
						del headers, add_header
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					extend((yield events))
					events = []
					addev = events.append
					# continues; no double CRLF yet.
				elif eof:
					# EOF must be > 0, otherwise it's the end of the headers.
					# Got a header within the constraints (max_header_size).

					# Spell out header tuple constructor for performance.
					eoi = find(b':', 0, eof) # Use find rather than split to avoid list().
					header = (bstrip(bytes(req[:eoi])), bstrip(bytes(req[eoi+1:eof])))
					del req[:eof+2]

					field = header[0].lower()
					if field in ctl_headers:
						ctl_headers[field].extend(x.strip() for x in header[1].split(b','))

					add_header(header)
					nheaders += 1
					pos = 0
					if nheaders > max_headers:
						addev((headers_ev, headers))
						addev((
							violation_ev,
							('limit', 'max_headers', nheaders, max_headers)
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith, req
						del headers, add_header
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])
			# :while not startswith(b"\r\n")

			# Emit remaining headers.
			if headers:
				addev((headers_ev, headers))

			# Avoid holding old references in case of future subsitution.
			del headers, add_header

			# Terminator
			addev(EOH)

			# Trim trailing CRLF.
			del req[:2]
		# : if eoh == -1

		keep_alive = b'keep-alive' in cn

		if cl:
			if len(cl) > 1:
				addev((
					warning_ev,
					('protocol', 'multiple-content-lengths',
						"multiple length values present", cl)
				))

			try:
				ctl_headers[b'content-length'] = cl = size = int(cl[0])
			except ValueError:
				addev((
					violation_ev,
					('protocol', 'invalid-header',
						"Content-Length could not be interpreted as an integer", cl[0])
				))
				addev((bypass_ev, req))

				del find, extend, buflen, startswith, req
				req = (yield events)
				del events, addev
				while True:
					req = (yield [(bypass_ev, req)])

		if te:
			if te[-1] == b'chunked':
				# If C-L was specified, override it here.
				chunk_size = -1
				size = -1
				body_ev = chunk_ev
			elif b'chunked' in te:
				addev((
					warning_ev,
					('protocol', 'misplaced-chunked-coding',
						"chunked coding was present but not final", te)
				))

		# headers processed, redetermine has_body given &size.

		if has_body is True and size is None:
			# size was not initialized so it should assume there's no body
			if keep_alive is not True and is_client:
				del find, extend, buflen, startswith
				addev((content_ev, req))
				req = (yield events)
				del events, addev
				while True:
					# Connection is closed
					req = (yield [(content_ev, req)])
			else:
				has_body = False
				size = 0

		# End of headers; emit body, if any.
		pos = 0
		while size:
			while chunk_size == -1:
				##
				# Transfer-Encoding: chunked; read the chunk size line
				eof = find(b"\r\n", pos, max_chunk_line_size)
				if eof == -1:
					# no terminator, need more data

					# make sure we are not exceeding the max chunk line size
					if buflen() > max_chunk_line_size:
						addev((
							violation_ev,
							('limit', 'max_chunk_line_size', buflen(), max_chunk_line_size)
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith, req
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					# Update position to the end of buffer minus one so it's not
					# scanning for CRLF through data that it has already scanned.
					pos = max(buflen() - 1, 0)
					extend((yield events))
					events = []
					addev = events.append
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
						addev((violation_ev, ('protocol', 'chunk-field', chunk_field)))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith, req
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					del chunk_field
					size = chunk_size

			# Transfer known size.
			n = buflen()
			if n < size:
				# Buffer size is less than remainder.
				size = size - n
				body_size += n
				addev((body_ev, req))

				# Replace req entirely with the next input.
				# Loop only needs the size to progress,
				req = find = extend = buflen = startswith = None
				req = (yield events)
				events = []
				addev = events.append

				# Act nearly as a passthrough here when the size is known.
				n = len(req)
				while n < size:
					size = size - n
					body_size += n
					# Try to continue passing data through.
					req = (yield [(body_ev, req)])
					n = len(req)
				else:
					# Exceeded the remaining size, so its on the edge
					# Re-initialize buffer.
					req = bytearray(req)
					find = req.find
					extend = req.extend
					buflen = req.__len__
					startswith = req.startswith

			# &req is now larger than the remaining &size.
			# There is enough data to complete the body or chunk.

			if size:
				body_size += size
				addev((body_ev, req[0:size]))
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
				while not startswith(b"\r\n"):
					# continue until we get a CRLF
					if buflen() > 2:
						# req has content but it's not a CRLF? bad
						addev((
							violation_ev,
							('protocol', 'bad-chunk-terminator', req[:2])
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					extend((yield events))
					events = []
					addev = events.append

				assert req[0:2] == b"\r\n"

				del req[0:2]
				# end of chunks?
				if chunk_size != 0:
					# more chunks coming
					chunk_size = -1
					size = -1
				# else assert chunk_size == size == 0
		# :while size

		# Body termination indicator; but there may be trailers to parse.
		if has_body:
			# Used to signal the stream of EOF;
			# primarily useful to signal compression
			# transformations to flush the buffers.
			addev((body_ev, b""))

		if chunk_size == 0:
			# Chunking occurred, read and emit trailers.
			# Trailers are supposed to be declared ahead of time,
			# so it may be reasonable to thrown a violation.
			ntrailers = 0
			trailers = []
			eof = find(b"\r\n", 0, max_header_size)
			while eof != 0:
				if eof == -1:
					# No terminator, need more data.
					if trailers:
						addev((trailers_ev, trailers))
						trailers = []
					if buflen() > max_trailer_size:
						addev((
							violation_ev, ('limit', 'max_trailer_size', buflen())
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					extend((yield events))
					events = []
					addev = events.append
					# look for eof again
				elif eof:
					# found the terminator
					ntrailers += 1
					trailer = tuple(map(bytes, map(bastrip, req[:eof].split(b':', 1))))
					del req[0:eof+2]
					trailers.append(trailer)

					if eof > max_trailer_size:
						# Limit Violation
						addev((trailers_ev, trailers))
						del trailers
						addev((
							violation_ev, ('limit', 'max_trailer_size', eof)
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

					if ntrailers > max_trailers:
						# Limit Violation
						addev((trailers_ev, trailers))
						del trailers
						addev((
							violation_ev, ('limit', 'max_trailers', ntrailers)
						))
						addev((bypass_ev, req))

						del find, extend, buflen, startswith
						req = (yield events)
						del events, addev
						while True:
							req = (yield [(bypass_ev, req)])

				# find next end of field.
				eof = find(b"\r\n", 0, max_header_size)

			# remove the trailing CRLF
			del req[0:2]
			# Emit remaining headers.
			if trailers:
				addev((trailers_ev, trailers))
			# signals the end of trailers
			trailers = ()
			addev((trailers_ev, trailers))
		# chunk_size == 0

		# finish up by resetting size and emitting EOM on continuation
		size = None
		addev(EOM)
		if keep_alive is not True:
			if req:
				addev((bypass_ev, req))
			del find, extend, buflen, startswith, req
			req = (yield events)
			del events, addev
			while True:
				req = (yield [(bypass_ev, req)])
	else: # for message_number in range(...):
		# too many messages
		addev((violation_ev, ('limit', 'max_messages', max_messages)))
		del find, extend, buflen, startswith
		while True:
			addev((bypass_ev, req))
			req = (yield events)
			events = []
			addev = events.append
Disassembler = Tokenization

def disassembly(**config):
	"""
	# Returns an already started &Disassembler generator.
	"""
	global Disassembler
	d = Disassembler(**config)
	d.__next__()
	return d

def headers(headers, chain=itertools.chain.from_iterable, CRLF=protocoldata.CRLF, HFS=protocoldata.HFS):
	"""
	# Produce an iterator of &bytes instances making up a segment
	# of headers that can be joined into a buffer.
	"""
	return chain(((x[0], HFS, x[1], CRLF) for x in headers))
trailers = headers

@functools.lru_cache(16)
def chunk_size(length, CRLF=protocoldata.CRLF, hex=hex):
	return (b"%x\r\n" %(length,))

def chunk(data, len=len, CRLF=protocoldata.CRLF):
	"""
	# Returns a tuple of (chunk-size + CRLF, chunk-data, CRLF).

	# Joining data into a single buffer is avoided for the express
	# purpose of allowing the data buffer to be passed through.
	# In cases where a shared memory segment is referenced, this
	# can be critical for proper performance.

	# Currently, &Serialization will concatenate these, defeating
	# some of the purpose.

	#!/pl/python
		assert chunk(b"data") == (b"4\\r\\n", b"data", b"\\r\\n")
	"""
	return (chunk_size(len(data)), data, CRLF)

def Serialization(
		chunk_map = {
			ev_chunk: chunk,
			ev_content: lambda x: (x,),
			ev_bypass: lambda x: (x,),
			ev_message: lambda x: (),
		}
	):
	"""
	# Assemble HTTP events back into a sequences of bytes.
	"""

	events = (yield None)
	while True:
		buf = bytearray()
		append = buf.__iadd__
		seq = (buf,)

		for (t, v) in events:

			if t in chunk_map:
				# Default to concatenation of event payload.
				for x in (chunk_map[t](v)):
					append(x)
			elif t == 0: # rline_ev
				append(b" ".join(v))
				append(b"\r\n")
			else: # {heavers_ev, trailers_ev}
				if not v:
					# end of headers
					append(b"\r\n")
				else:
					append(b"\r\n".join(y[0] + b": " + y[1] for y in v))
					append(b"\r\n")

		events = (yield seq)
Assembler = Serialization

def assembly(**config):
	"""
	# Return a started &Assembler generator.
	"""
	global Assembler
	g = Assembler()
	g.__next__()
	return g
