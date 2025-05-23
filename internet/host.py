"""
# Endpoint and Service type for referencing internet addresses for
# Internet Protocol version 4 and 6.
"""
import typing
import ipaddress

class Service(int):
	"""
	# Internet port identifier. Empty subclass for identification purposes.
	"""
	__slots__ = ()

	valid_range = (0, 0xFFFF)
	system_range = (0, 1024)
	epheremal_range = (49152, 0xFFFF)

	def valid(self):
		"""
		# Whether or not the Service port is within the standard range.
		"""

		return self >= 0 and self <= 0xFFFF

	def system(self):
		"""
		# Whether or not the Service port is considered a 'well known' port.
		"""

		return self >= 0 and self < 1024

	def ephemeral(self):
		"""
		# Whether or not the Service port is considered an 'ephemeral' port by IANA.
		"""

		return self >= 49152 and self <= 0xFFFF

	@classmethod
	def from_name(Class, name):
		return common_services[name]

# A subset of IANA's list to the primary services used by the Internet.
common_services = {
	'domain': Service(53),

	'http': Service(80),
	'https': Service(443),
	'ftp': Service(21),
	'ftps': Service(990),

	'ssh': Service(22),
	'telnet': Service(23),

	'smtp': Service(25),
	'kerberos': Service(88),
	'ntp': Service(123),
	'bgp': Service(179),
	'irc': Service(194),
	'ldap': Service(389),
}
common_services['dns'] = common_services['domain']

class Endpoint(tuple):
	"""
	# A precise Endpoint for internet addresses and local sockets.
	"""
	__slots__ = ()

	address_types = (ipaddress.IPv4Address, ipaddress.IPv6Address)

	@classmethod
	def create_ip4(Class, string, port, Type=ipaddress.IPv4Address):
		"""
		# Create an IPv4 Endpoint Instance
		"""

		return Class((Type(string), Service(port)))

	@classmethod
	def create_ip6(Class, string, port, Type=ipaddress.IPv6Address):
		"""
		# Create an IPv6 Endpoint Instance
		"""

		return Class((Type(string), Service(port)))

	@property
	def protocol(self, str=str):
		"""
		# Addressing protocol; 4 or 6
		"""

		return 'ip' + str(self.address.version)

	@property
	def interface(self):
		"""
		# The &ipaddress typed address.
		"""
		return self[0]
	address = interface

	@property
	def port(self):
		"""
		# The &Service of the endpoint.
		"""

		return self[1]

	def __str__(self):
		"""
		# "<address>:<port>" representation suitable for interpolation into
		# an IRI network location.
		"""

		if self.interface.version == 6:
			return '[' + str(self.interface) + ']:' + str(self.port)
		else:
			return str(self.interface) + ':' + str(self.port)

	def __repr__(self):
		m = __name__
		n = self.__class__.__name__
		p = self.protocol
		i = str(self.interface)

		return "%s.%s.create_%s(%r, %r)" %(m, n, p, i, self.port)

	def __hash__(self):
		return hash((self.protocol, self.interface, self.port))

	@classmethod
	def create(Class, interface, port, construct=ipaddress.ip_address):
		"""
		# Create an IPv4 or IPv6 endpoint based on the type detected from the string.

		# The &ipaddress type will be selected by the &ipaddress.ip_address function.
		"""
		return Class((construct(interface), Service(port)))

class Reference(tuple):
	"""
	# A domain name referencing a set of endpoints.

	# References are actually service references for a specific domain. They
	# consist of protocol, address, port, and service fields that define
	# the reference. Normally, protocol is "dns" and implies system DNS.

	# Protocol variations can be used to describe more complicated name resolutions.
	"""
	__slots__ = ()

	fields = (
		'protocol',
		'address',
		'port',
		'service',
	)

	@property
	def protocol(self) -> str:
		"""
		# Resolution protocol to use to extract endpoints from &address. Usually, `'internet-names'`.
		"""
		return self[0]

	@property
	def address(self) -> object:
		"""
		# The unencoded domain name.
		"""
		return self[1]

	@property
	def port(self) -> Service:
		"""
		# The resolved or overridden port for the service.
		# Usually, this is &None as the &service will refer to the desired &Service port
		# or the resolver will manage a 
		"""
		return self[2]

	@property
	def service(self) -> str:
		"""
		# The actual service name being referred to.
		# Used by resolvers that support service name resolution.
		"""
		return self[3]

	def __str__(self):
		"""
		# Formatted reference for canonical printing.
		# Return "<service>:[<protocol>]<name>:<port>".
		"""
		return "%s:[%s]%s:%s" %(self.service, self.protocol, self.address, self.port)

	def __repr__(self):
		m = __name__
		n = self.__class__.__name__

		return "%s.%s((%r, %r, %r, %r))" %((m, n,) + self)

	@classmethod
	def from_domain(Class, name, service, port = None):
		if port is None:
			port = common_services[service]

		return Class(('internet-names', name, port, service))

def realize(struct:dict, scheme=None, host=None, port=None) -> typing.Union[Reference, Endpoint]:
	"""
	# Construct an &Endpoint or &Reference from &struct.

	#!syntax/python
		# Usual case:
		from fault.internet import ri
		target = host.realize(ri.parse(url))
	"""

	host = struct['host']
	port = struct.get('port', port)
	scheme = struct.get('scheme', scheme)

	onlydigits = all(map(str.isdigit, host.split('.', 3)))
	if onlydigits:
		if port is None:
			port = common_services[scheme]
		endpoint = Endpoint.create_ip4(host, port)
	else:
		# either domain or ip6
		if ':' in host:
			# ipv6
			host = host[1:-1]
			if port is None:
				port = common_services[scheme]
			endpoint = Endpoint.create_ip6(host, port)
		else:
			# needs name resolution
			endpoint = Reference.from_domain(host, scheme, port=port)

	return endpoint
