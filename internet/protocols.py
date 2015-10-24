"""
Information and mappings regarding common ciphers and security related protocols.
"""
import collections

class Struct(tuple):
	__slots__ = ()
	_fields = ()
	_nfields = 0

	@property
	def orderedmap(self, zip = zip, dict = collections.OrderedDict):
		return dict(zip(self._fields, self))

	@property
	def pairs(self, zip = zip):
		return zip(self._fields, self)

	@classmethod
	def construct(typ, **kw):
		l = list(typ._fields)
		for i, k in zip(range(typ._nfields), l):
			l[i] = kw[k]
		return typ(l)

class Organization(Struct):
	"""
	Information About an Organization
	"""
	__slots__ = ()
	_fields = ('domain', 'sector',)

class Protocol(Struct):
	"""
	Information about a protocol.
	"""
	__slots__ = ()
	_fields = (
		'organization',
		'identifier',
		'name',
		'version',
	)
	_nfields = len(_fields)

IETF = Organization(('ietf.org', 'rfc'))
Netscape = Organization(('netscape.org', None))

#: Security
transport_security = tuple(map(Protocol,[
	(Netscape, None, "SSL", "1.0"),
	(IETF, 6176, "SSL", "2.0"),
	(IETF, 6101, "SSL", "3.0"),
	(IETF, 2246, "TLS", "1.0"),
	(IETF, 4346, "TLS", "1.1"),
	(IETF, 5246, "TLS", "1.2"),
]))

#: Structures used for Public Key Infrastructure
pki_structs = tuple(map(Protocol,[
	(IETF, 5280, "X509", None),
]))

#: Protocols identified as insecure or not applicable.
insecure = set(transport_security[:2])
