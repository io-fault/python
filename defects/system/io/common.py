"""
# Common tools and tests employed across fault.defects.system.io tests.
"""
import pickle
import threading
import contextlib
import os
import socket
import time
from ....system import io
from ....system import network
from ....system import kernel
from ....system import thread

def allocpipe(A):
	r, w = os.pipe()
	return (
		io.alloc_input(r),
		io.alloc_output(w)
	)

def allocsockets(A):
	s1, s2 = socket.socketpair()
	s1.setblocking(False)
	s2.setblocking(False)
	s1 = io.alloc_octets(os.dup(s1.fileno()))
	s2 = io.alloc_octets(os.dup(s2.fileno()))
	return s1 + s2

def allocports(A):
	s1, s2 = socket.socketpair()
	s1.setblocking(False)
	s2.setblocking(False)
	s1 = io.alloc_ports(os.dup(s1.fileno()))
	s2 = io.alloc_ports(os.dup(s2.fileno()))
	return s1 + s2

ralloc_index = {
	io.Octets: bytearray,
}

def rallocate(channel, quantity):
	return ralloc_index[channel.__class__](quantity)

class Terminated(Exception):
	pass

class Delta(tuple):
	__slots__ = ()

	@property
	def channel(self):
		return self[0]

	@property
	def demand(self):
		return self[-1]

	@property
	def termination(self):
		if self[0].terminated:
			return self[0].port
		return None

	@property
	def terminated(self):
		return self[4]

	@property
	def resource(self):
		return self[1]

	@property
	def slice(self):
		return self[2]

	@property
	def transferred(self):
		if self[2] is not None and self[1] is not None:
			return self[1][self[2]]
		return None

	@classmethod
	def construct(typ, channel):
		s = channel.slice()
		x = channel.transfer()
		if s is not None:
			assert channel.sizeof_transfer() == s.stop - s.start
		a = None
		if channel.exhausted:
			a = channel.acquire
		return typ((channel, channel.resource, s, x, channel.terminated, a))

def snapshot(array, list=list, map=map, construct=Delta.construct):
	# list() is invoked here as materialization of the
	# snapshot is needed in cases where the cycle exits.
	return list(map(construct, array.transfer()))

def cycle(array):
	with array:
		return snapshot(array)

def loop(deliver, array, cycle=cycle, snapshot=snapshot):
	"""
	# Continuously &deliver transfers enqueued into the &array.
	"""

	while not array.terminated:
		with array:
			deliver(snapshot(array))
	try:
		deliver(cycle(array))
	except io.TransitionViolation:
		pass

class ArrayActionManager(object):
	"""
	# Manages the Array cycle in a separate thread to avoid inline management
	# of event collection.
	"""

	def __init__(self):
		self.array = io.Array()
		self.cycled = thread.amutex()
		self.cycles = 0
		self.effects = {}
		self.deadend = []

	def view(self):
		"""
		# Utility function for displaying the contents of a Array.
		"""

		r = self.array.resource
		for x in r:
			re = x.resource
			print(
				'polarity:', x.polarity,
				'terminated:', x.terminated,
				'endpoint:', x.endpoint(),
				'resource', bytes(re) if re else None
			)
		else:
			print('eoj')

	def force(self):
		self.array.force()

	def cycle(self, activity):
		with self.cycled:
			for x in activity:
				# append all events.
				# for testing, we're primarily interested in
				# the sequence for a given channel.
				self.effects.get(x.channel, self.deadend.append)(x)
				self.cycles += 1

	def loop(self):
		loop(self.cycle, self.array)

	@contextlib.contextmanager
	def thread(self):
		t = threading.Thread(target = self.loop)
		try:
			t.start()
			yield
		finally:
			self.array.terminate()
			t.join()
			del self.deadend[:]

	@contextlib.contextmanager
	def manage(self, ct):
		try:
			self.effects.update(ct.effects)
			for x in ct.channels:
				self.array.acquire(x)
			yield
		finally:
			ct.terminate()
			for x in self.delta():
				terms = [y.terminated for y in ct.channels]
				if all(terms):
					# all have been terminated
					break
			for x in ct.channels:
				x.port.raised()
			for k in ct.effects:
				del self.effects[k]
			del ct

	def delta(self):
		"""
		# Wait for a cycle to occur; use to regulate transfer progress.
		"""

		self.array.force()
		i = 0

		while True:
			if i != self.cycles:
				with self.cycled:
					i = self.cycles
					# Hold the cycle lock while integrating the changes.
					yield i
			else:
				# Avoid using a lock here to simplify termination.
				time.sleep(0.0001)
				yield None

class Events(object):
	"""
	# For cases involving single Channels.

	# No autoread setup.
	"""
	def __init__(self, *channels):
		self.channels = channels
		self.events = []
		self.effects = {}

		for x in channels:
			self.effects[x] = self.events.append

	def terminate(self):
		for x in self.channels:
			x.terminate()

	def _term_check(self):
		for x in self.channels:
			if x.terminated:
				raise Terminated(x, self)

	def raised(self):
		for x in self.channels:
			x.port.raised()

	def vacancies(self):
		i = 0
		for x in self.channels:
			if x.resource is None:
				i += 1
		return i

	@property
	def terminated(self):
		for x in self.channels:
			if x.terminated:
				return True
		return False

	def exhausted(self, limit=None):
		i = 0
		for x in self.events[:limit]:
			if x.demand:
				i += 1
		return i

	@property
	def exhaustions(self):
		return self.exhausted()

	@property
	def sockets(self):
		payload = []
		for x in self.events:
			if x.transferred:
				payload += x.transferred
		return payload

	def get_data(self, limit=None):
		payload = bytearray(0)
		for x in list(self.events)[:limit]:
			xfer = x.transferred
			if xfer is not None:
				payload.extend(xfer)
		return payload

	@property
	def data(self):
		return self.get_data()

	def clear(self, limit=None):
		del self.events[:limit]

	def setup_read(self, quantity):
		for x in self.channels:
			x.acquire(rallocate(x, quantity))

	def setup_write(self, resource):
		for x in self.channels:
			x.acquire(resource)

class Endpoint(object):
	"""
	# For cases involving send and receives.
	"""

	def __init__(self, channels, bufsize = 64):
		self.channels = channels
		self.read_channel, self.write_channel = channels

		self.read_events = []
		self.write_events = []
		self.read_length = 0
		self.default_bufsize = bufsize

		self.effects = {
			self.read_channel: self._read_event,
			self.write_channel: self.write_events.append,
		}

	def _read_event(self, activity):
		d = activity.demand
		if activity.transferred:
			self.read_length += len(activity.transferred)
		if d is not None:
			# chain reads
			d(rallocate(activity.channel, self.default_bufsize))
		self.read_events.append(activity)

	def terminate(self):
		for x in self.channels:
			x.terminate()

	def _write_term_check(self):
		if self.write_channel.terminated:
			raise Terminated(self.write_channel, self) from self.write_channel.port.exception()

	def _read_term_check(self):
		if self.read_channel.terminated:
			raise Terminated(self.read_channel, self) from self.read_channel.port.exception()

	@property
	def read_exhaustions(self):
		self._read_term_check()
		return sum([1 if x.demand is not None else 0 for x in self.read_events])

	@property
	def write_exhaustions(self):
		self._write_term_check()
		return sum([1 if x.demand is not None else 0 for x in self.write_events])

	@property
	def read_payload_int(self):
		self._read_term_check()
		payload = rallocate(self.read_channel, 0)
		for x in self.read_events:
			if x.transferred:
				payload += x.transferred
		return payload

	@property
	def read_payload(self):
		self._read_term_check()
		payload = bytearray(0)
		for x in self.read_events:
			if x.transferred:
				payload += x.transferred
		return payload

	@property
	def units_written(self):
		self._write_term_check()
		return sum([
			len(x.transferred) for x in self.write_events if x.transferred
		])

	@property
	def units_read(self):
		self._write_term_check()
		return sum([
			len(x.transferred) for x in self.read_events if x.transferred
		])

	def clear(self):
		del self.read_events[:]
		del self.write_events[:]
		self.read_length = 0

	def clear_reads(self):
		del self.read_events[:]
		self.read_length = 0

	def clear_writes(self):
		del self.write_events[:]

	def setup_read(self, rallocation):
		self._read_term_check()
		self.read_channel.acquire(rallocate(self.read_channel, rallocation))

	def setup_write(self, resource):
		self._write_term_check()
		self.write_channel.acquire(resource)

class Objects(object):
	"""
	# Endpoint that transfers objects.
	"""

	def __init__(self, channels):
		self.channels = channels
		self.read_channel, self.write_channel = channels
		self.read_state = None
		self._read_buf = bytearray(0)
		self.received_objects = []

		self.bytes_written = 0
		self.send_complete = 0

		self.effects = {
			self.read_channel: self._read_event,
			self.write_channel: self._write_event,
		}
		self.read_channel.acquire(rallocate(self.read_channel, 128))

	def _read_event(self, activity):
		d = activity.demand
		xfer = activity.transferred
		if xfer is not None:
			self._read_buf += xfer
			try:
				objs = pickle.loads(self._read_buf)
			except:
				pass
			else:
				self.received_objects.append(objs)
				del self._read_buf[:]
		if d is not None:
			d(rallocate(activity.channel, 512))

	def _write_event(self, activity):
		if activity.demand is not None:
			self.send_complete += 1

	def terminate(self):
		for x in self.channels:
			x.terminate()

	def _write_term_check(self):
		if self.write_channel.terminated:
			raise Terminated(self.write_channel, self) from self.write_channel.port.exception()

	def _read_term_check(self):
		if self.read_channel.terminated:
			raise Terminated(self.read_channel, self) from self.read_channel.port.exception()

	@property
	def done_writing(self):
		self._write_term_check()
		return self.write_channel.exhausted

	def clear(self):
		del self.received_objects[:]

	def send(self, obj):
		self._write_term_check()
		d = pickle.dumps(obj)
		self.write_channel.acquire(d)

def exchange_nothing(test, am, client, server):
	pass

def exchange_few_bytes(test, am, client, server):
	client.setup_write(b'')
	client.setup_read(0)
	for x in am.delta():
		if client.write_exhaustions:
			break
	test/client.write_exhaustions >= 1

	server.setup_write(b'11')
	for x in am.delta():
		if client.read_exhaustions:
			break
	test/client.read_exhaustions >= 1

	for x in am.delta():
		if server.write_exhaustions:
			break
	test/server.units_written == 2
	test/server.write_exhaustions >= 1

	server.setup_read(1)
	for x in am.delta():
		if client.units_read == 2:
			break

	client.clear()
	server.clear()

	# there are resources, so force a zero transfer
	server.read_channel.force()
	client.read_channel.force()

	for x in am.delta():
		if server.read_events and client.read_events:
			break
	# inspect the channel directly, read_data
	test/bytes(server.read_events[-1].transferred) == b''
	test/bytes(client.read_events[-1].transferred) == b''

def exchange_many_bytes(test, am, client, server):
	client_sends = b'This is a string for the server to receive.'
	server_sends = b'This is a string for the client to receive.'

	server.setup_read(len(client_sends))
	client.setup_read(len(server_sends))

	# there are resources, so force a zero transfer
	server.read_channel.force()
	client.read_channel.force()
	for x in am.delta():
		if server.read_events and client.read_events:
			break
	# inspect the channel directly, read_data
	test/bytes(server.read_events[0].transferred) == b''
	test/bytes(client.read_events[0].transferred) == b''

	client.setup_write(client_sends)
	server.setup_write(server_sends)
	for x in am.delta():
		if server.read_exhaustions:
			break

	for x in am.delta():
		if client.read_exhaustions:
			break

	for x in am.delta():
		if server.write_exhaustions:
			break

	for x in am.delta():
		if client.write_exhaustions:
			break

	test/client.read_payload == server_sends
	test/server.read_payload == client_sends

def exchange_many_bytes_many_times(test, am, client, server):
	server.setup_read(0)
	client.setup_read(0)

	for x in range(32):
		client_sends = b'This is a string for the server to receive.'
		server_sends = b'This is a string for the client to receive.......'

		client.setup_write(client_sends)
		server.setup_write(server_sends)

		for x in am.delta():
			if server.write_exhaustions:
				break

		for x in am.delta():
			if client.write_exhaustions:
				break

		for x in am.delta():
			if client.read_length == len(server_sends):
				break;
		test/client.read_payload == server_sends

		for x in am.delta():
			if server.read_length == len(client_sends):
				break
		test/server.read_payload == client_sends

		client.clear()
		server.clear()

def exchange_kilobytes(test, am, client, server):
	server.setup_read(0)
	client.setup_read(0)

	send = b'All work and no play....makes jack a dull boy...'
	total_size = (1024 * len(send))
	client.setup_write(send * 1024)
	for x in am.delta():
		if client.write_exhaustions:
			client.clear()
			break
	for x in am.delta():
		if server.read_length == total_size:
			break

transfer_cases = [
	exchange_nothing,
	exchange_few_bytes,
	exchange_many_bytes,
	exchange_many_bytes_many_times,
	exchange_kilobytes,
]

def echo_objects(test, am, client, server):
	echos = [
		[1,2,3],
		"UNICODE",
		2**256,
		{'foo':'bar'}
	]

	for obj in echos:
		server.send(obj)
		for x in am.delta():
			if client.received_objects:
				break
		client.send(client.received_objects[0])
		client.clear()
		for x in am.delta():
			if server.received_objects:
				break

		test/server.received_objects[0] == obj
		server.clear()

object_transfer_cases = [
	echo_objects,
]

def stream_listening_connection(test, version, address):
	am = ArrayActionManager()
	if_p = network.Endpoint(version, address, None, 'octets')
	fd = network.service(if_p)
	s_endpoint = network.receive_endpoint(fd)

	def Accept(ls=fd):
		kpv = kernel.Ports.allocate(1)
		ic = 0
		while kpv[0] == -1:
			kernel.accept_ports(ls, kpv)
			ic += 1
			if ic > 512:
				raise Exception("accept limit reached")
		return kpv

	with am.thread():
		for exchange in transfer_cases:
			peer_ep = s_endpoint
			pfd = network.connect(peer_ep)
			client_channels = io.alloc_octets(pfd)

			client_channels[0].port.raised()
			# Adjusting the kernel's buffer size isn't critical, but
			# do so to exercise the code path for all stream types.
			client_channels[0].resize_exoresource(1024 * 8)
			client_channels[1].resize_exoresource(1024 * 8)
			client = Endpoint(client_channels)

			test.isinstance(client_channels[0].port.freight, str)
			test.isinstance(client_channels[1].port.freight, str)

			with am.manage(client):
				c_endpoint = client.write_channel.endpoint()
				r_endpoint = client.read_channel.endpoint()

				fd = Accept()[0]

				server_channels = io.alloc_octets(fd)
				server = Endpoint(server_channels)
				with am.manage(server):
					sr_endpoint = server.read_channel.endpoint()
					sw_endpoint = server.write_channel.endpoint()

					if isinstance(sr_endpoint, network.Endpoint) and isinstance(c_endpoint, network.Endpoint):
						test/sr_endpoint.address == c_endpoint.address
						# should be None for endpoints without ports.
						test/sr_endpoint.port == c_endpoint.port

					if isinstance(sw_endpoint, network.Endpoint) and isinstance(r_endpoint, network.Endpoint):
						test/sw_endpoint.address == r_endpoint.address
						# should be None for endpoints without ports.
						test/sw_endpoint.port == r_endpoint.port

					exchange(test, am, client, server)
				test/server.channels[0].terminated == True
				test/server.channels[1].terminated == True
				test/server.channels[0].exhausted == False
				test/server.channels[1].exhausted == False

				# Endpoint information is still accessible until the system finishes
				# the disconnect. Loop until it disappears.
				ep0, ep1 = [x.endpoint for x in server.channels]
				active = True
				while active:
					for x in am.delta():
						break
					active = bool(ep0() is not None or ep1() is not None)

				test/server.channels[0].endpoint() == None
				test/server.channels[1].endpoint() == None
				del server

			test/client.channels[0].terminated == True
			test/client.channels[1].terminated == True
			test/client.channels[0].exhausted == False
			test/client.channels[1].exhausted == False

			# Endpoint information is still accessible until the system finishes
			# the disconnect. Loop until it disappears.
			ep0, ep1 = [x.endpoint for x in client.channels]
			active = True
			while active:
				for x in am.delta():
					break
				active = bool(ep0() is not None or ep1() is not None)
			test/client.channels[0].endpoint() == None
			test/client.channels[1].endpoint() == None
			del client

	test/am.array.terminated == True
