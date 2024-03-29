"""
# Check integrations of internet.http and kernel.http
"""
import itertools
from ...web import http as library

from ...kernel import flows
from ...kernel import core as kcore
from ...kernel import io as kio
from ..kernel import library as testlib

default_headers = [
	(b'Host', b'test.fault.io'),
	(b'Connection', b'keep-alive'),
]

def req(*headers, host=b'test.fault.io', version=b'HTTP/1.1', uri=b'/test/fault.io.http', method=b'GET',
		body=b'', ctype=b'text/plain', chunks=()
	):
	init = b'%s %s %s\r\n' % (method, uri, version)
	additional = [
		(b'Host', host),
		(b'Connection', b'keep-alive'),
	]

	if body:
		l = str(len(body))
		additional.extend([
			(b'Content-Length', l.encode('ascii')),
			(b'Content-Type', ctype),
		])
	elif chunks:
		additional.extend([
			(b'Transfer-Encoding', b'chunked'),
			(b'Content-Type', ctype),
		])
		sizes = [hex(x).encode('ascii')[2:] + b'\r\n' for x in map(len, chunks)]
		body = b''.join((x+y+b'\r\n') for x,y in zip(sizes, chunks))
		body += b'0\r\n\r\n'

	headers = itertools.chain(additional, headers)
	header_data = b'\r\n'.join(map(b'%s: %s'.__mod__, headers))

	return (init + header_data + b'\r\n\r\n' + body,)

def test_ranges(test):
	"""
	# Check Range header parsing.
	"""
	test/list(library.ranges(0, None)) == [(0, 0)]
	test/list(library.ranges(123, None)) == [(0, 123)]
	test/list(library.ranges(100, None)) == [(0, 100)]

	# HTTP Ranges are inclusive.
	test/list(library.ranges(100, b"bytes=0-0")) == [(0, 1)]
	test/list(library.ranges(100, b"bytes=0-100")) == [(0, 101)]

	# Missing starts means last n-bytes.
	test/list(library.ranges(100, b"bytes=-50")) == [(50, 100)]

allocate_transparent = (lambda x: (('line+headers',) + x, b'VERSION'))

def test_fork_headers_no_content(test):
	"""
	# - &library.fork
	"""
	closed = False
	def close():
		nonlocal closed
		closed = True
	overflow = []

	shared = {
		'disposition': 'server',
		'version': b'HTTP/1.1',
	}
	g = library.fork(shared, allocate_transparent, close, overflow.append)
	g.send(None)

	r_open, r_close = list(g.send(req()))
	qual, iline, headers = r_open[-1]
	test/r_open[0] == flows.fe_initiate
	test/r_close[0] == flows.fe_terminate
	test/r_close[1] == r_open[1]

	test/qual == 'line+headers'
	test/iline[0] == b'GET'
	test/iline[1] == b'/test/fault.io.http'
	test/iline[2] == b'HTTP/1.1'
	hd = dict(headers)
	test/hd[b'Host'] == b'test.fault.io'

	# Content-Length body.
	r_open, *body, r_close = list(g.send(req(body=b'content')))
	qual, iline, headers = r_open[-1]
	test/qual == 'line+headers'
	test/r_open[0] == flows.fe_initiate
	test/r_close[0] == flows.fe_terminate
	test/r_close[1] == r_open[1]

	test/iline[0] == b'GET'
	test/iline[1] == b'/test/fault.io.http'
	test/iline[2] == b'HTTP/1.1'
	hd = dict(headers)
	test/hd[b'Host'] == b'test.fault.io'

	total_content = b''
	for event in body:
		test/event[1] == r_open[1]
		total_content += b''.join(event[2])
	test/total_content == b'content'

	# Chunked body.
	r_open, *body, r_close = list(g.send(req((b'Connection', b'close'), chunks=(b'first\n', b'second\n'))))
	layer = r_open[1]
	qual, iline, headers = r_open[-1]
	test/r_open[0] == flows.fe_initiate
	test/r_close[0] == flows.fe_terminate
	test/r_open[1] == r_close[1]

	test/iline[0] == b'GET'
	test/iline[1] == b'/test/fault.io.http'
	test/iline[2] == b'HTTP/1.1'
	hd = dict(headers)
	test/hd[b'Host'] == b'test.fault.io'
	test/hd[b'Connection'] == b'close'

	total_content = b''
	for event in body:
		test/event[1] == r_open[1]
		total_content += b''.join(event[2])
	test/total_content == b'first\nsecond\n'

def test_join(test):
	import collections

	shared = {
		'disposition': 'server',
		'version': b'HTTP/1.1',
	}

	overflow = []
	def ident(x):
		l, h = x
		if dict(h).get(b'Transfer-Encoding') == b'chunked':
			return None
		return 0

	allocate_transparent = (lambda x: ((x + (ident(x),)), b'VERSION'))
	initiate_transparent = (lambda x,y: y)

	j = library.join(shared, initiate_transparent)
	g = library.fork(shared, allocate_transparent, (lambda: None), overflow.append)
	g.send(None); j.send(None)

	r = req()
	events = list(g.send(r))
	layer = events[0][-1]
	test/b''.join(list(j.send(events))) == r[0]

	r = req(chunks=(b'first\n', b'second\n'))
	events = list(g.send(r))
	layer = events[0][-1]
	test/b''.join(list(j.send(events))) == r[0]

	r = req(body=(b'first\n' + b'second\n'))
	events = list(g.send(r))
	layer = events[0][-1]
	test/b''.join(list(j.send(events))) == r[0]

def test_Structures_local(test):
	"""
	# - &library.Structures

	# Check caching of local headers.
	"""
	headers = [
		(b'Server', b'fault/0'),
		(b'Host', b'fault.io'),
		(b'Custom', b'data'),
	]
	s = library.Structures(headers, b'Custom')

	test/s.cache[b'host'] == b'fault.io'
	test/s.cache[b'custom'] == b'data'

def test_Structures_cookies(test):
	"""
	# - &library.Structures
	"""
	pass

def test_TXProtocol_initiate_request(test):
	"""
	# - &library.TXProtocol
	"""
	shared = {
		'version': b'HTTP/1.1',
		'disposition': 'client',
	}
	l = []
	add = (lambda x: l.extend(x.i_correlate()))
	ctx, S = testlib.sector()

	end = flows.Collection.list()
	pf = library.TXProtocol(shared, library.TXProtocol.initiate_server_request)

	io = ('test', None), (flows.Channel(), end)
	T = kio.Transport.from_endpoint(io)
	rxtx = kcore.Transaction.create(T)
	S.dispatch(rxtx)

	c = T.tp_connect(add,
		(('http', None), (flows.Channel(), pf)),
	)

	ctx(1)

	inv = (b'GET', b'/test', [], None)
	(channel_id, connect), = c.i_allocate()
	connect(inv, None)
	ctx(2)
	test/end.c_storage[0][0] == (b"GET /test HTTP/1.1" + b"\r\n"*3)

def test_RXProtocol_allocate_request(test):
	"""
	# - &library.RXProtocol
	"""
	shared = {
		'version': b'HTTP/1.1',
		'disposition': 'client',
	}
	l = []
	add = (lambda x: l.extend(x.i_correlate()))
	ctx, S = testlib.sector()

	end = flows.Collection.list()
	pf = library.RXProtocol(shared, library.RXProtocol.allocate_client_request)

	io = ('test', None), (flows.Channel(), end)
	T = kio.Transport.from_endpoint(io)
	rxtx = kcore.Transaction.create(T)
	S.dispatch(rxtx)

	c = T.tp_connect(add,
		(('http', None), (pf, flows.Channel())),
	)

	pf.f_transfer(req())
	ctx(2)
	inv = l[0][1]
	test/inv == (b'GET', b'/test/fault.io.http', default_headers)

def test_client_transport(test):
	"""
	# - &library.RXProtocol
	# - &library.TXProtocol
	"""
	l = []
	add = (lambda x: l.extend(x.i_correlate()))

	ctx, S = testlib.sector()
	end = flows.Collection.list()
	start = flows.Channel()

	t = kio.Transport.from_endpoint((('test', None), (start, end)))
	rxtx = kcore.Transaction.create(t)
	S.dispatch(rxtx)
	ctx(1)

	m = t.tp_connect(add, library.allocate_client_protocol())
	ctx(1)
	inv = (b'GET', b'/test', [], None)
	(channel_id, connect), = m.i_allocate()
	connect(inv, None)
	ctx(1)
	test/end.c_storage[0][0] == (b"GET /test HTTP/1.1" + b"\r\n"*3)

	start.f_transfer([b"HTTP/1.1 200 OK\r\n"])
	start.f_transfer([b"Content-Length: 100\r\n\r\n"])
	start.f_transfer([b"X"*100])
	start.f_transfer([b"\r\n"])
	ctx(1)

	connect_input = l[0][2]
	r = flows.Receiver(connect_input)
	S.dispatch(r)
	received_content = flows.Collection.list()
	r.f_connect(received_content)
	S.dispatch(received_content)
	r.f_transfer(None)
	ctx(1)

	xfer = b''.join(map(b''.join, received_content.c_storage))
	test/xfer == b"X"*100
	ctx(1)
	test/r.terminated == True

def test_server_transport(test):
	"""
	# - &library.RXProtocol
	# - &library.TXProtocol
	"""
	l = []
	add = (lambda x: l.extend(x.i_accept()))

	ctx, S = testlib.sector()
	end = flows.Collection.list()
	start = flows.Channel()

	t = kio.Transport.from_endpoint([('test', None), (start, end)])
	S.dispatch(kcore.Transaction.create(t))
	ctx(1)

	m = t.tp_connect(add, library.allocate_server_protocol())
	ctx(1)

	start.f_transfer([b"POST /test HTTP/1.1\r\n"])
	start.f_transfer([b"Content-Length: 100\r\n\r\n"])
	start.f_transfer([b"X"*100])
	start.f_transfer([b"\r\n"])
	ctx(1)

	connect_output = l[0][0]
	connect_input = l[1][0][2]

	r = flows.Receiver(None)
	S.dispatch(r)
	received_content = flows.Collection.list()
	r.f_connect(received_content)
	S.dispatch(received_content)
	connect_input(r)
	ctx(1)

	# Received
	xfer = b''.join(map(b''.join, received_content.c_storage))
	test/xfer == b"X"*100
	ctx(1)
	test/r.terminated == True

	relay = flows.Relay(m.i_catenate, 1)
	S.dispatch(relay)
	connect_output((b'200', b'OK', [(b'Content-Length', b'200')], 200), relay)
	relay.f_transfer([b"Y"*200])
	relay.f_terminate()
	ctx(1)

	xfer = b''.join(map(b''.join, end.c_storage))
	expect = b"HTTP/1.1 200 OK\r\n"
	expect += b"Content-Length: 200\r\n"
	expect += b"\r\n"
	expect += b"Y"*200

	test/xfer == expect
	ctx(1)
	test/r.terminated == True

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
