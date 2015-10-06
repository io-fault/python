"""
Endpoint and Service type for referencing internet addresses for
Internet Protocol version 4 and 6.
"""
import ipaddress

class Service(int):
	"""
	Internet port identifier. Empty subclass for identification purposes.
	"""
	__slots__ = ()

	def valid(self):
		"Whether or not the Service port is within the standard range."

		return self >= 0 and self <= 0xFFFF

	def system(self):
		"Whether or not the Service port is considered a 'well known' port."

		return self >= 0 and self < 1024

	def ephemeral(self):
		"Whether or not the Service port is considered an 'ephemeral' port by IANA."

		return self >= 49152 and self < 0xFFFF

	@classmethod
	def from_name(Class, name):
		global common_services
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
	Endpoint type for internet addresses.
	"""
	__slots__ = ()

	address_types = (ipaddress.IPv4Address, ipaddress.IPv6Address)

	@classmethod
	def create_ip4(Class, string, port, Type=ipaddress.IPv4Address):
		"Create an IPv4 Endpoint Instance"

		return Class((Type(string), Service(port)))

	@classmethod
	def create_ip6(Class, string, port, Type=ipaddress.IPv6Address):
		"Create an IPv6 Endpoint Instance"

		return Class((Type(string), Service(port)))

	@property
	def protocol(self, str=str):
		"Addressing protocol; 4 or 6"

		return 'ip' + str(self.address.version)

	@property
	def interface(self):
		"The &ipaddress typed address."
		return self[0]

	address = interface

	@property
	def port(self):
		"The &Service of the endpoint."

		return self[1]

	def __str__(self):
		"""
		"<address>:<port>" representation suitable for interpolation into
		an IRI network location.
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
		Create an IPv4 or IPv6 endpoint based on the type detected from the string.

		The &ipaddress type will be selected by the &ipaddress.ip_address function.
		"""
		return Class((construct(interface), Service(port)))

class Reference(tuple):
	"""
	A domain name referencing a set of endpoints.

	References are actually service references for a specific domain. They
	consist of protocol, address, port, and service fields that define
	the reference. Normally, protocol is "dns" and implies system DNS.

	Protocol variations can be used to describe more complicated name resolutions.
	"""
	__slots__ = ()

	@property
	def protocol(self):
		"Resolution protocol. Usually, DNS."
		return self[0]

	@property
	def address(self):
		"The unencoded domain name."
		return self[1]

	@property
	def port(self):
		"The resolved or overridden port for the service."
		return self[2]

	@property
	def service(self):
		"The actual service name being referred to."
		return self[3]

	def __str__(self):
		"""
		Formatted reference for canonical printing.
		Return "<service>:[<protocol>]<name>:<port>".
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

		return Class(('domain', name, port, service))
