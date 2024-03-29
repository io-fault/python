"""
# &..kernel protocol adapters for transport security contexts.
"""
import weakref
import types
import importlib.machinery

from ..context import weak
from ..kernel import flows
from ..system import identity
from ..project import system as lsf

def get_application_context(application='http'):
	import os
	from ..system import query
	from ..system import files

	if 'SECURITY' in os.environ:
		return files.Path.from_absolute(os.environ['SECURITY'])

	return (query.home() / '.pki' / application)

class Violation(Exception):
	"""
	# Security Context restriction violation.

	# Usually caused by implementation errors, violations are
	# abstractions used to provide a symbolic identifier for
	# the restriction that was violated.

	# [ Properties ]
	# /identifier/
		# The symbolic identifier used to describe the error.
	# /description/
		# An implementation specific description of the error.
	"""

	def __init__(self, identifier, description):
		self.identifier = identifier
		self.description = description

	def __str__(self):
		return "%s: %s" %(self.identifier, self.description)

def load_context(route, type:str, name='pki'):
	sys, arch = identity.root_execution_context()
	product = route@'if/kprotocol'

	ctx = lsf.Context()
	ctx.connect(product)
	ctx.load()
	for pj in ctx.iterprojects():
		if pj.factor.identifier == type:
			break
	else:
		raise Exception("security context did not have a kprotocol %s project" %(type,))

	var = lsf.types.Variants(sys, arch)
	dllpath = ctx.image(var, pj.factor@"extensions"/name)
	loader = importlib.machinery.ExtensionFileLoader(name, str(dllpath))
	return loader.load_module()

def load(type:str, application='http', name='pki'):
	"""
	# Load the extension module for the given &type and &application.

	# [ Parameters ]
	# /type/
		# The identifier for the adapter's protocol.
		# Normally, (id)`kprotocol-client` or (id)`kprotocol-server`.
	# /application/
		# The symbolic name for the application.
		# Defaults to (id)`http`.
	"""
	route = get_application_context(application)
	return load_context(route, type, name=name)

class SecuredTransmit(flows.Protocol):
	"""
	# Transport stack entry for secured output.
	# Holds a weak reference to the corresponding &SecuredReceive instance
	# using &stx_receive_channel.
	"""

	_stx_receive_closed = False

	def stx_receive_closed(self):
		"""
		# Signal endpoint recognizing when the corresponding receive
		# has seen a transport protocol level termination.
		"""
		self._stx_receive_closed = True

		if self.terminating:
			if self.p_shared.close():
				self.p_drain()
			self._f_terminated()

	def stx_receive_interrupt(self):
		"""
		# Wire closed without protocol shutdown.
		"""
		self._stx_receive_closed = True

		if self.terminating:
			self._f_terminated()
		else:
			self.fault(Exception("receive interrupted while transmit was active"))

	def f_terminate(self):
		if not self.functioning:
			return

		self.start_termination()

		if self.p_shared.close():
			self.p_drain()

class SecuredReceive(flows.Protocol):
	"""
	# Transport stack entry for secured input.
	# Holds a strong reference to the corresponding &SecuredTransmit instance
	# using &srx_transmit_channel.
	"""

	def interrupt(self):
		super().interrupt()
		self.srx_transmit_channel.stx_receive_interrupt()

	def p_terminated(self):
		self.start_termination()
		self.srx_transmit_channel.stx_receive_closed()

	def f_terminate(self):
		self.p_drain()

		if not self.terminating:
			self.srx_transmit_channel.stx_receive_interrupt()
		self._f_terminated()

def allocate(tls, Method=weak.Method, Reference=weakref.ref):
	"""
	# Construct a protocol stack pair using the given &tls instance.
	"""

	stx = SecuredTransmit(tls, None, tls.encipher)
	srx = SecuredReceive(tls, None, tls.decipher)

	srx.srx_transmit_channel = stx
	stx.stx_receive_channel = Reference(srx)

	drain = Method(stx.p_drain).zero
	tls.connect_transmit_ready(drain)

	ptermd = Method(srx.p_terminated).zero
	tls.connect_receive_closed(ptermd)

	return (srx, stx)
