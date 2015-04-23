"""
Endpoint and Service type for referencing connection addresses.
"""
import ipaddress

class Service(int):
	"""
	Internet port identifier. Empty subclass for identification purposes.
	"""
	pass

class Endpoint(tuple):
	"""
	Endpoint type for internet addresses.
	"""
	__slots__ = ()
	address_types = (ipaddress.IPv4Address, ipaddress.IPv6Address)

	@property
	def protocol(self, str = str):
		'Addressing protocol; 4 or 6'
		return 'ip' + str(self.address.version)

	@property
	def address(self):
		return self[0]

	@property
	def port(self):
		return self[1]

	def __str__(self):
		if self.address.version == 6:
			return '[' + str(self.address) + ']:' + str(self.port)
		else:
			return str(self.address) + ':' + str(self.port)

	def __hash__(self):
		return hash((self.address, self.port))

	@classmethod
	def create(Class, identifier, port, type = ipaddress.ip_address):
		"""
		Primary method for creating an endpoint.
		The &ipaddress type will be selected by the &ipaddress.ip_address function.
		"""
		return Class((type(identifier), Service(port)))
