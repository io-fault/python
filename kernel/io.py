"""
# I/O Transaction Contexts for managing transfers and protocol transports.

# I/O is managed using three types: &Transfer, &Transport, and &Interface.
# &Transfer is the Transaction that manages the flows supporting a bidirectional or unidirecitonal
# stream.
"""
import typing
import itertools

from . import core
from . import flows

class Transfer(core.Context):
	"""
	# Context managing a *single* sequence of &flows.Channel instances.

	# [ Properties ]
	# /io_transport/
		# The &Transport context that is directly facilitating the transfer.
		# &None if none.
	"""

	def actuate(self):
		self.provide('transfer')

	io_transport = None

	@property
	def io_complete(self) -> bool:
		return self.terminated or self.terminating

	def io_flow(self, series, Terminal=flows.Terminal) -> flows.Terminal:
		"""
		# Connect a sequence of &flows.Channel instances to a new &flows.Terminal
		# instance that signals the &Transfer when the Flow has completed.

		# The &flows.Terminal created and dispatched will be returned and the &Transfer flow
		# count will be incremented.
		"""

		dispatch = self.controller.dispatch

		end = Terminal(self._io_transfer_terminated)
		for x in series:
			dispatch(x)
		dispatch(end)

		downstream = end
		for x in reversed(series):
			x.f_connect(downstream)
			downstream = x

		return end

	def io_capture(self, series):
		"""
		# Perform the transfer of the given &series while capturing all of the events that leave
		# the Transfer Context.
		"""
		t = self.io_flow()
		c = flows.Collection.list()
		t.f_connect(c)
		self.xact_dispatch(c)
		self._capture = c.c_storage

	def _io_check_terminate(self):
		if self.xact_empty():
			self.finish_termination()
		# Dispatch timeout?

	def _io_transfer_terminated(self, terminal):
		"""
		# Count to two and exit the transaction.
		"""
		self.start_termination()
		self.enqueue(self._io_check_terminate)

class Transport(Transfer):
	"""
	# The Transaction Context that manages the stack of protocols
	# used to facilitate arbitrary I/O streams.
	"""

	def __init__(self):
		self._tp_channels = {}
		self._tp_stack = []

	@classmethod
	def from_stack(Class, entries):
		"""
		# Push the protocol channels on to the stack.
		"""
		tp = Class()
		channels = tp._tp_channels
		stack = tp._tp_stack

		for state, pair in entries:
			channels[state] = pair
			stack.append(state)

		return tp

	def actuate(self):
		self.provide('transport')

	def tp_connect(self, mitre):
		"""
		# Connect the given mitre series, &mitre, to the configured transport stack.
		# Usually called after dispatching an instance created with &from_stack.
		"""
		end = []
		start = []
		for x in self._tp_stack:
			rc, sc = self._tp_channels[x]
			end.append(sc)
			start.append(rc)

		end.reverse()
		return self.io_flow(start + [flows.Division(), mitre, flows.Catenation()] + end)

	def tp_push(self, state, io):
		"""
		# Push the protocol channels on to the stack.
		"""

		self._tp_channels[state] = io
		top = self._tp_stack[-1]
		self._tp_stack.append(state)
		dispatch = self.controller.dispatch
		top[0].f_inject(io[0])
		top[1].f_inject(io[1])
		dispatch(io[0])
		dispatch(io[1])

	def tp_protocol_terminated(self, state):
		"""
		# Called by a protocol stack entry when both sides of the state have been closed.
		"""
		pass

	def tp_remove(self, state):
		i = self._tp_stack.index(state)
		del self._tp_stack[i:i+1]
		r, s = self._tp_channels.pop(state)
		return r.p_overflow, s.p_overflow

	def tp_get(self, label):
		for i in self._tp_stack:
			l, x = i
			if label == l:
				return x, self._tp_channels[i]

		raise LookupError(label)

class Interface(core.Executable):
	"""
	# Executable context managing a logical interface.
	"""

	def if_route(self, packet, chain=itertools.chain.from_iterable):
		"""
		# Route the accepted connections.
		"""

		source, event = packet
		for io_pair in chain(event):
			self.xact_dispatch(f)

	def if_install(self, *kports):
		"""
		# Given file descriptors, install a new set of flows
		# accepting sockets from the given listening sockets.
		"""

		acquire = self.system.acquire_listening_sockets

		for listen in acquire(kports):
			x, flow = listen

			if_r = (x.interface, x.port)
			if_t.f_connect(null)

			flow.f_connect(if_t)
			flow.f_transfer(None) # Start allocating file descriptor arrays.

def security_operations(transport):
	"""
	# Construct the input and output operations used by &.library.Transports instances.
	# All implementations accessible from &..security expose the same features,
	# so &operations is implementation independent.
	"""

	return (
		(transport.decipher, transport.pending_input, transport.pending_output),
		(transport.encipher, transport.pending_output, transport.pending_input),
	)

def dispatch(xact, *flows:typing.Sequence[flows.Channel]):
	"""
	# Dispatch a set of a flows within the Transaction as connected Transfers.
	"""

	for x in reversed(flows):
		xf = Transfer()
		sub = Transaction.create(xf)
		xact.dispatch(sub)
		xf.critical(functools.partial(xf.io_flow, *x))
