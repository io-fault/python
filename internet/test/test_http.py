from .. import http as module

# Sanity
def test_module_protocol(test):
	'Disassembler' in test/dir(module)
	'disassembly' in test/dir(module)
	'Assembler' in test/dir(module)
	'assembly' in test/dir(module)

def test_Disassembler_complete_request(test):
	data = b"GET / HTTP/1.0\r\nHost: host\r\n\r\n"
	state = module.disassembly()
	events = state.send(data)
	x = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [(b'Host', b'host')]),
		module.EOH,
		module.EOM,
	]
	test/x == events

def test_Disassembler_complete_response(test):
	data = b"HTTP/1.0 200 OK\r\nHost: host\r\n\r\n"
	state = module.disassembly()
	events = state.send(data)
	x = [
		(module.Event.rline, (b'HTTP/1.0', b'200', b'OK')),
		(module.Event.headers, [(b'Host', b'host')]),
		module.EOH,
		module.EOM,
	]
	test/x == events

def test_Disassembler_response_nobody(test):
	data = b"HTTP/1.0 204 OK\r\nHost: host\r\n\r\n"
	state = module.disassembly()
	events = state.send(data)
	x = [
		(module.Event.rline, (b'HTTP/1.0', b'204', b'OK')),
		(module.Event.headers, [(b'Host', b'host')]),
		module.EOH,
		module.EOM,
	]
	test/x == events

def test_Disassembler_bypass(test):
	"""
	Check that data received after a connection close message
	is forwarded inside a bypass event.
	"""
	data = b"GET / HTTP/1.0\r\nHost: host\r\nConnection: close\r\n\r\nBYPASS"
	state = module.disassembly()
	events = state.send(data)
	x = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [(b'Host', b'host'), (b'Connection', b'close')]),
		module.EOH,
		module.EOM,
		(module.Event.bypass, b'BYPASS'),
	]
	test/x == events
	test/state.send(b'More') == [(module.Event.bypass, b'More')]

def test_Disassembler_chunked_1(test):
	"""
	Test one chunk.
	"""
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
\r
"""
	state = module.disassembly()
	output = state.send(data)
	x = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		module.EOH,
		(module.Event.chunk, b'fffff'),
		(module.Event.chunk, b''),
		(module.Event.trailers, ()),
		module.EOM,
	]
	test/x == output

def test_Disassembler_chunked_2(test):
	"""
	Test one chunk with fragmented data.
	"""
	data1 = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5"""
	data2 = b"""\r
fff"""
	data3 = b"""ff\r
0\r
\r
"""
	g = module.disassembly()
	eventseq1 = g.send(data1)
	eventseq2 = g.send(data2)
	eventseq3 = g.send(data3)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
				(b'Transfer-Encoding', b'chunked'),
				(b'Host', b'host')
			],
		),
		module.EOH,
	]
	x2 = [
		(module.Event.chunk, b'fff'),
	]
	x3 = [
		(module.Event.chunk, b'ff'),
		(module.Event.chunk, b''),
		(module.Event.trailers, ()),
		module.EOM,
	]

	test/x1 == eventseq1
	test/x2 == eventseq2
	test/x3 == eventseq3

def test_Disassembler_chunked_trailers_1(test):
	"""
	Test one chunk.
	"""
	data = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
Trailer: value\r
\r
"""
	g = module.disassembly()
	eventseq1 = g.send(data)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff'),
		(module.Event.chunk, b''),
		(module.Event.trailers, [(b'Trailer', b'value')]),
		(module.Event.trailers, ()),
		module.EOM,
	]
	test/x1 == eventseq1

def test_Disassembler_chunked_trailers_2(test):
	"""
	Test one chunk.
	"""
	data1 = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
Trailer: value\r
"""
	data2 = b"""Trailer: value2\r
\r
"""
	g = module.disassembly()
	eventseq1 = g.send(data1)
	eventseq2 = g.send(data2)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff',),
		(module.Event.chunk, b'',),
		(module.Event.trailers, [
				(b'Trailer', b'value')
		]),
	]
	x2 = [
		(module.Event.trailers, [
			(b'Trailer', b'value2')
		]),
		(module.Event.trailers, ()),
		module.EOM,
	]
	test/x1 == eventseq1
	test/x2 == eventseq2

def test_Disassembler_trailers_limit_bypass(test):
	"""
	Test the trailer size limit and the subsequent bypass.
	"""

	data = b"GET / HTTP/1.0\r\nTransfer-Encoding: chunked\r\nHost: host\r\n\r\n"
	data += b"5\r\nfffff\r\n0\r\nTrailer: value\r\n\r\n"

	# Case where the trailer EOF is known.
	g = module.disassembly(max_trailer_size=4)
	eventseq1 = g.send(data)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff'),
		(module.Event.chunk, b''),
		(module.Event.trailers, [(b'Trailer', b'value')]),
		(module.Event.violation, ('limit', 'max_trailer_size', 14)),
		(module.Event.bypass, b'\r\n'),
	]
	test/x1 == eventseq1
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

	data = b"GET / HTTP/1.0\r\nTransfer-Encoding: chunked\r\nHost: host\r\n\r\n"
	data += b"5\r\nfffff\r\n0\r\nTrailer: value"

	# Case where the trailer EOF is *not* known.
	g = module.disassembly(max_trailer_size=4)
	eventseq1 = g.send(data)
	x2 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff'),
		(module.Event.chunk, b''),
		(module.Event.violation, ('limit', 'max_trailer_size', 14)),
		(module.Event.bypass, b'Trailer: value'),
	]
	test/x2 == eventseq1
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_max_trailers(test):
	"""
	Test the trailer size limit and the subsequent bypass.
	"""

	data = b"GET / HTTP/1.0\r\nTransfer-Encoding: chunked\r\nHost: host\r\n\r\n"
	data += b"5\r\nfffff\r\n0\r\nTrailer: value\r\n\r\n"

	# Case where the trailer EOF is known.
	g = module.disassembly(max_trailers=0)
	eventseq1 = g.send(data)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff'),
		(module.Event.chunk, b''),
		(module.Event.trailers, [(b'Trailer', b'value')]),
		(module.Event.violation, ('limit', 'max_trailers', 1)),
		(module.Event.bypass, b'\r\n'),
	]
	test/x1 == eventseq1
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_chunked_separated_size(test):
	"""
	Test one chunk with fragmented data.
	"""
	data1 = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
"""
	data2 = b'1'
	data3 = b'0'
	data4 = b'\r'
	data5 = b'\n'
	data6 = b'X' * (0x10 - 5)
	data7 = b'Y' * (0x10 - (0x10 - 5))
	data8 = b'\r'
	data9 = b'\n0\r\n\r'
	data10 = b'\n'

	g = module.disassembly();
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(module.Event.headers, ()),
	]
	test/x1 == g.send(data1)
	test/[] == g.send(data2)
	test/[] == g.send(data3)
	test/[] == g.send(data4)
	test/[(module.Event.chunk, b'')] == g.send(data5)

	x2 = [(module.Event.chunk, b'X' * (0x10 - 5))]
	test/x2 == list(g.send(data6))

	x3 = [(module.Event.chunk, b'Y' * (0x10 - (0x10 - 5)))]
	test/x3 == g.send(data7)
	test/[] == g.send(data8)

	x4 = [(module.Event.chunk, b'')]
	test/x4 == g.send(data9)

	x5 = [(module.Event.trailers, ()), module.EOM]
	test/x5 == g.send(data10)

def test_Disassembler_crlf_prefix_strip(test):
	data = b"\r\n\r\nGET / HTTP/1.1\r\n"
	g = module.disassembly()
	eventseq1 = g.send(data)
	x1 = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
	]
	test/x1 == eventseq1

def test_Disassembler_pipelined(test):
	mrequest = b'''GET /index.html HTTP/1.1\r
Host: localhost\r
Content-Length: 20\r
\r
''' + b'A' * 20 + b'''\r
POST /data.html HTTP/1.1\r
Host: localhost\r
Content-Length: 30\r
\r
''' + b'Bad' * 10
	g = module.disassembly()

	x1 = [
		(module.Event.rline, (b'GET', b'/index.html', b'HTTP/1.1')),
		(module.Event.headers, [(b'Host', b'localhost'), (b'Content-Length', b'20')]),
		(module.Event.headers, ()),
		(module.Event.content, b'A' * 20),
		(module.Event.content, b''),
		module.EOM,

		(module.Event.rline, (b'POST', b'/data.html', b'HTTP/1.1')),
		(module.Event.headers, [(b'Host', b'localhost'), (b'Content-Length', b'30')]),
		(module.Event.headers, ()),
		(module.Event.content, b'Bad' * 10),
		(module.Event.content, b''),
		module.EOM,
	]
	eventseq1 = g.send(mrequest)
	test/x1 == eventseq1

def test_Disassembler_type_error(test):
	# XXX: moved away from HTTP exceptions in favor of violation events
	g = module.disassembly()
	test/TypeError ^ (lambda: g.send(123))

def test_Disassembler_limit_line_too_large(test):
	data = b'GET / HTTP/1.1'
	g = module.disassembly(max_line_size = 8)
	r = g.send(data)
	test/r == [
		(module.Event.violation, ('limit', 'max_line_size', 8)),
		(module.Event.bypass, data),
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_line_too_large_with_eof(test):
	data = b'GET / HTTP/1.1\r\nHost: host\r\n\r\n'
	g = module.disassembly(max_line_size = 4)
	r = g.send(data)
	test/r == [
		(module.Event.violation, ('limit', 'max_line_size', 4)),
		(module.Event.bypass, data),
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_invalid_content_length(test):
	"""
	Check that the value error is properly reported.
	"""
	data = b"GET / HTTP/1.0\r\nHost: host\r\nContent-Length: vz@\r\nConnection: close\r\n\r\nBYPASS"
	state = module.disassembly()
	events = state.send(data)
	x = [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(module.Event.headers, [
			(b'Host', b'host'),
			(b'Content-Length', b'vz@'),
			(b'Connection', b'close'),
		]),
		(module.Event.headers, ()),
		(module.Event.violation,
			('protocol', 'Content-Length', bytearray(b'vz@'))),
		(module.Event.bypass, b'BYPASS'),
	]
	test/x == events
	test/state.send(b'More') == [(module.Event.bypass, b'More')]

def test_Disassembler_invalid_chunk_field(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
zzz\r
fffff\r
0\r
\r"""
	g = module.disassembly()
	r = g.send(data)
	test/r == [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(module.Event.headers, ()),
		(module.Event.violation,
			('protocol', 'chunk-field', bytearray(b'zzz'))),
		(module.Event.bypass, bytearray(b'fffff\r\n0\r\n\r')),
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_chunk_no_terminator(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff
0\r
\r"""
	g = module.disassembly()
	r = g.send(data)
	test/r == [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(module.Event.headers, ()),
		(module.Event.chunk, b'fffff'),
		(module.Event.violation,
			('protocol', 'bad-chunk-terminator', b'\n0')),
		(module.Event.bypass, bytearray(b'\n0\r\n\r')),
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_max_chunksize(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
50\r
fffff\r
0\r
\r"""
	g = module.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(module.Event.headers, ()),
		(module.Event.violation, ('limit', 'max_chunk_line_size', 15, 1)),
		(module.Event.bypass, bytearray(b'50\r\nfffff\r\n0\r\n\r'))
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_max_chunksize_split(test):
	output = []
	data = b"GET / HTTP/1.1\r\nTransfer-Encoding: chunked\r\nHost: host\r\n\r10"
	g = module.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(module.Event.headers, ()),
		(module.Event.violation, ('limit', 'max_chunk_line_size', 15, 1)),
		(module.Event.bypass, bytearray(b'50\r\nfffff\r\n0\r\n\r'))
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_max_chunksize_split(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
ffffffds"""
	g = module.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(module.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(module.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(module.Event.headers, ()),
		(module.Event.violation, ('limit', 'max_chunk_line_size', 11, 1)),
		(module.Event.bypass, bytearray(b'5\r\nffffffds')),
	]
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_header_too_large(test):
	output = []
	data = b"GET / HTTP/1.1\r\nFoo: bar"
	# feed it two while expecting one
	g = module.disassembly(max_header_size = 2)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, limit) = vio
	test/vio == module.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_header_size'
	test/limit == 2
	test/byp[0] == module.Event.bypass
	test/byp[1] == b"""Foo: bar"""
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_header_too_large_with_eof(test):
	output = []
	data = b"GET / HTTP/1.1\r\nFirst: value\r\nSecond: value\r\n"
	# feed it two while expecting one
	g = module.disassembly(max_header_size = 2)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, limit) = vio
	test/vio == module.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_header_size'
	test/limit == 2
	test/byp[0] == module.Event.bypass
	test/byp[1] == b"First: value\r\nSecond: value\r\n"
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_limit_header_too_many(test):
	output = []
	data = b"GET / HTTP/1.1\r\nFoo: bar\r\n\r"
	# feed it two while expecting one
	g = module.disassembly(max_headers = 0)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, count, max) = vio
	test/vio == module.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_headers'
	test/count == 1
	test/max == 0
	test/byp[0] == module.Event.bypass
	test/byp[1] == b"\r"
	test/g.send(b'Bypassed') == [(module.Event.bypass, b'Bypassed')]

def test_Disassembler_exercise_zero_writes(test):
	output = []
	data = b"HTTP/1.0 400 Bad Request\r\nFoo: bar\r\n\r"
	g = module.disassembly()
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(data) == [
		(module.Event.rline, (b'HTTP/1.0', b'400', b'Bad Request')),
		(module.Event.headers, [(b'Foo', b'bar')])
	]

def test_headers(test):
	samples = [
		(b'Foo: bar\r\n', [(b'Foo', b'bar')]),
		(b'Foo: Bar\r\nContent-Length: 5\r\n',
			[(b'Foo', b'Bar'), (b'Content-Length', b'5')])
	]
	for expected, sdata in samples:
		test/expected == b''.join(module.headers(sdata))

def test_chunk(test):
	samples = [
		(b'3\r\nfoo\r\n', b'foo'),
		(b'6\r\nfoobar\r\n', b'foobar'),
		(hex(100).encode('ascii')[2:] + b'\r\n' + (b'x' * 100) + b'\r\n', b'x' * 100),
	]
	for expected, data in samples:
		test/expected == b''.join(module.chunk(data))

def test_assemble(test):
	# out of order assembly
	reqs = [
		b"""GET /foo HTTP/1.1\r
Foo: bar\r
\r
""",
		b"""POST / HTTP/1.1\r
Content-Length: 0\r
\r
"""
	]

	d = module.disassembly()
	a = module.assembly()

	for x in reqs:
		de = d.send(x)
		ad = a.send(de)
		test/b''.join(ad) == x

def test_assemble_ooo(test):
	"""
	Validate that we don't validate output state.
	Assembly presumes the user knows what she is doing.
	"""
	# out of order assembly
	g = module.assembly()
	r = g.send([(module.Event.content, b'data')])
	test/r == (b'data',)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
