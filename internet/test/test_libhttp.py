from .. import libhttp

# Sanity
def test_module_protocol(test):
	'Disassembler' in test/dir(libhttp)
	'disassembly' in test/dir(libhttp)
	'Assembler' in test/dir(libhttp)
	'assembly' in test/dir(libhttp)

def test_dis_complete_request(test):
	data = b"""GET / HTTP/1.0\r
Host: host\r
\r
"""
	state = libhttp.disassembly()
	events = state.send(data)
	x = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [(b'Host', b'host')]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.content, b''),
	]
	test/x == events

def test_dis_chunked_1(test):
	'test one chunk'
	data = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
\r
\r
"""
	state = libhttp.disassembly()
	output = state.send(data)
	x = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.chunk, b'fffff'),
		(libhttp.Event.chunk, b''),
		(libhttp.Event.trailers, ()),
	]
	test/x == output

def test_dis_chunked_2(test):
	'test one chunk with fragmented data'
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
\r
"""
	g = libhttp.disassembly()
	eventseq1 = g.send(data1)
	eventseq2 = g.send(data2)
	eventseq3 = g.send(data3)
	x1 = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [
				(b'Transfer-Encoding', b'chunked'),
				(b'Host', b'host')
			],
		),
		(libhttp.Event.headers, ()),
	]
	x2 = [
		(libhttp.Event.chunk, b'fff'),
	]
	x3 = [
		(libhttp.Event.chunk, b'ff'),
		(libhttp.Event.chunk, b''),
		(libhttp.Event.trailers, ()),
	]

	test/x1 == eventseq1
	test/x2 == eventseq2
	test/x3 == eventseq3

def test_dis_chunked_trailers_1(test):
	'test one chunk'
	data = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
\r
Trailer: value\r
\r
"""
	g = libhttp.disassembly()
	eventseq1 = g.send(data)
	x1 = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.chunk, b'fffff'),
		(libhttp.Event.chunk, b''),
		(libhttp.Event.trailers, [(b'Trailer', b'value')]),
		(libhttp.Event.trailers, ()),
	]
	test/x1 == eventseq1

def test_dis_chunked_trailers_2(test):
	'test one chunk'
	data1 = b"""GET / HTTP/1.0\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff\r
0\r
\r
Trailer: value\r
"""
	data2 = b"""Trailer: value2\r
\r
"""
	g = libhttp.disassembly()
	eventseq1 = g.send(data1)
	eventseq2 = g.send(data2)
	x1 = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [
			(b'Transfer-Encoding', b'chunked'),
			(b'Host', b'host')
		]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.chunk, b'fffff',),
		(libhttp.Event.chunk, b'',),
		(libhttp.Event.trailers, [
				(b'Trailer', b'value')
		]),
	]
	x2 = [
		(libhttp.Event.trailers, [
			(b'Trailer', b'value2')
		]),
		(libhttp.Event.trailers, ()),
	]
	test/x1 == eventseq1
	test/x2 == eventseq2

def test_dis_chunked_separated_size(test):
	'test one chunk with fragmented data'
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
	data9 = b'\n0\r\n\r\n\r'
	data10 = b'\n'

	g = libhttp.disassembly();
	x1 = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.0')),
		(libhttp.Event.headers, [(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(libhttp.Event.headers, ()),
	]
	test/x1 == g.send(data1)
	test/[] == g.send(data2)
	test/[] == g.send(data3)
	test/[] == g.send(data4)
	test/[] == g.send(data5)

	x2 = [(libhttp.Event.chunk, b'X' * (0x10 - 5))]
	test/x2 == g.send(data6)

	x3 = [(libhttp.Event.chunk, b'Y' * (0x10 - (0x10 - 5)))]
	test/x3 == g.send(data7)
	test/[] == g.send(data8)

	x4 = [(libhttp.Event.chunk, b'')]
	test/x4 == g.send(data9)

	x5 = [(libhttp.Event.trailers, ())]
	test/x5 == g.send(data10)

def test_dis_crlf_prefix_strip(test):
	data = b"""\r
\r
GET / HTTP/1.1\r
"""
	g = libhttp.disassembly()
	eventseq1 = g.send(data)
	x1 = [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
	]
	test/x1 == eventseq1

def test_dis_pipelined(test):
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
	g = libhttp.disassembly()

	x1 = [
		(libhttp.Event.rline, (b'GET', b'/index.html', b'HTTP/1.1')),
		(libhttp.Event.headers, [(b'Host', b'localhost'), (b'Content-Length', b'20')]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.content, b'A' * 20),
		(libhttp.Event.content, b''),

		(libhttp.Event.rline, (b'POST', b'/data.html', b'HTTP/1.1')),
		(libhttp.Event.headers, [(b'Host', b'localhost'), (b'Content-Length', b'30')]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.content, b'Bad' * 10),
		(libhttp.Event.content, b''),
	]
	eventseq1 = g.send(mrequest)
	test/x1 == eventseq1

def test_dis_type_error(test):
	# XXX: moved away from HTTP exceptions in favor of violation events
	g = libhttp.disassembly()
	test/TypeError ^ (lambda: g.send(123))

def test_dis_limit_line_too_large(test):
	data = b'GET / HTTP/1.1'
	g = libhttp.disassembly(max_line_size = 8)
	r = g.send(data)
	test/r == [
		(libhttp.Event.violation, ('limit', 'max_line_size', 8)),
		(libhttp.Event.bypass, data),
	]

def test_dis_limit_line_too_large_with_eof(test):
	data = b'GET / HTTP/1.1\r\n'
	g = libhttp.disassembly(max_line_size = 8)
	r = g.send(data)
	test/r == [
		(libhttp.Event.violation, ('limit', 'max_line_size', 8)),
		(libhttp.Event.bypass, data),
	]

def test_dis_invalid_chunk_field(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
zzz\r
fffff\r
0\r
\r"""
	g = libhttp.disassembly()
	r = g.send(data)
	test/r == [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(libhttp.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.violation,
			('protocol', 'chunk-field', bytearray(b'zzz'))),
		(libhttp.Event.bypass, bytearray(b'fffff\r\n0\r\n\r')),
	]

def test_dis_chunk_no_terminator(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
fffff
0\r
\r"""
	g = libhttp.disassembly()
	r = g.send(data)
	test/r == [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(libhttp.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
		(libhttp.Event.headers, ()),
		(libhttp.Event.chunk, b'fffff'),
		(libhttp.Event.violation,
			('protocol', 'bad-chunk-terminator', b'\n0')),
		(libhttp.Event.bypass, bytearray(b'\n0\r\n\r')),
	]

def test_dis_limit_max_chunksize(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
50\r
fffff\r
0\r
\r"""
	g = libhttp.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(libhttp.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(libhttp.Event.headers, ()),
		(libhttp.Event.violation, ('limit', 'max_chunk_line_size', 15, 1)),
		(libhttp.Event.bypass, bytearray(b'50\r\nfffff\r\n0\r\n\r'))
	]

def test_dis_limit_max_chunksize_split(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
10"""
	g = libhttp.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(libhttp.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(libhttp.Event.headers, ()),
		(libhttp.Event.violation, ('limit', 'max_chunk_line_size', 15, 1)),
		(libhttp.Event.bypass, bytearray(b'50\r\nfffff\r\n0\r\n\r'))
	]

def test_dis_limit_max_chunksize_split(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Transfer-Encoding: chunked\r
Host: host\r
\r
5\r
ffffffds"""
	g = libhttp.disassembly(max_chunk_line_size = 1)
	r = g.send(data)
	test/r == [
		(libhttp.Event.rline, (b'GET', b'/', b'HTTP/1.1')),
		(libhttp.Event.headers,
			[(b'Transfer-Encoding', b'chunked'), (b'Host', b'host')]),
			(libhttp.Event.headers, ()),
		(libhttp.Event.violation, ('limit', 'max_chunk_line_size', 11, 1)),
		(libhttp.Event.bypass, bytearray(b'5\r\nffffffds')),
	]

def test_dis_limit_too_many_messages(test):
	output = []
	g = libhttp.disassembly(max_messages = 0)
	r = g.send(b'GET')
	test/r[-2] == (libhttp.Event.violation, ('limit', 'max_messages', 0))

	data = b"""GET / HTTP/1.1\r
\r
GET /foo HTTP/1.1\r
\r"""
	# feed it two while expecting one
	g = libhttp.disassembly(max_messages = 1)
	r = g.send(data)
	test/r[-2] == (libhttp.Event.violation, ('limit', 'max_messages', 1))

def test_dis_limit_header_too_large(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Foo: bar"""
	# feed it two while expecting one
	g = libhttp.disassembly(max_header_size = 2)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, limit) = vio
	test/vio == libhttp.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_header_size'
	test/limit == 2
	test/byp[0] == libhttp.Event.bypass
	test/byp[1] == b"""Foo: bar"""

def test_dis_limit_header_too_large_with_eof(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Foo: bar\r
\r"""
	# feed it two while expecting one
	g = libhttp.disassembly(max_header_size = 2)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, limit) = vio
	test/vio == libhttp.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_header_size'
	test/limit == 2
	test/byp[0] == libhttp.Event.bypass
	test/byp[1] == b"""Foo: bar\r
\r"""

def test_dis_limit_header_too_many(test):
	output = []
	data = b"""GET / HTTP/1.1\r
Foo: bar\r
\r"""
	# feed it two while expecting one
	g = libhttp.disassembly(max_headers = 0)
	r = g.send(data)
	vio, byp = r[-2:]
	vio, (viotype, limitation, count, max) = vio
	test/vio == libhttp.Event.violation
	test/viotype == 'limit'
	test/limitation == 'max_headers'
	test/count == 1
	test/max == 0
	test/byp[0] == libhttp.Event.bypass
	test/byp[1] == b"\r"

def test_dis_exercise_zero_writes(test):
	output = []
	data = b"""HTTP/1.0 400 Bad Request\r
Foo: bar\r
\r"""
	g = libhttp.disassembly()
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(b'') == []
	test/g.send(data) == [
		(libhttp.Event.rline, (b'HTTP/1.0', b'400', b'Bad Request')),
		(libhttp.Event.headers, [(b'Foo', b'bar')])
	]

def test_headers(test):
	samples = [
		(b'Foo: bar\r\n', [(b'Foo', b'bar')]),
		(b'Foo: Bar\r\nContent-Length: 5\r\n',
			[(b'Foo', b'Bar'), (b'Content-Length', b'5')])
	]
	for expected, sdata in samples:
		test/expected == b''.join(libhttp.headers(sdata))

def test_chunk(test):
	samples = [
		(b'3\r\nfoo\r\n', b'foo'),
		(b'6\r\nfoobar\r\n', b'foobar'),
		(hex(100).encode('ascii')[2:] + b'\r\n' + (b'x' * 100) + b'\r\n', b'x' * 100),
	]
	for expected, data in samples:
		test/expected == b''.join(libhttp.chunk(data))

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

	d = libhttp.disassembly()
	a = libhttp.assembly()

	for x in reqs:
		de = d.send(x)
		ad = a.send(de)
		test/ad == x

def test_assemble_ooo(test):
	"""
	Validate that we don't validate output state. Assembly presumes the user knows what she
	is doing.
	"""
	# out of order assembly
	g = libhttp.assembly()
	r = g.send([(libhttp.Event.content, b'foo')])
	test/r == b'foo'
