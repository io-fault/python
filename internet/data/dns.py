"""
Data for working with DNS.

This module primarily consists of mapping of :py:class:`str` identifiers to
numeric identifiers for DNS types, classes, and errors.
"""

#: A mapping of Record Types to their numeric identifier.
type_to_id = {
	'A': 1,
	'NS': 2,
	'MD': 3,
	'MF': 4,
	'CNAME': 5,
	'SOA': 6,
	'MB': 7,
	'MG': 8,
	'MR': 9,
	'NULL': 10,
	'WKS': 11,
	'PTR': 12,
	'HINFO': 13,
	'MINFO': 14,
	'MX': 15,
	'TXT': 16,
	'RP': 17,
	'AFSDB': 18,
	'X25': 19,
	'ISDN': 20,
	'RT': 21,
	'NSAP': 22,
	'NSAP-PTR': 23,
	'SIG': 24,
	'KEY': 25,
	'PX': 26,
	'GPOS': 27,
	'AAAA': 28,
	'LOC': 29,
	'NXT': 30,
	'EID': 31,
	'NIMLOC': 32,
	'SRV': 33,
	'ATMA': 34,
	'NAPTR': 35,
	'KX': 36,
	'CERT': 37,
	'A6': 38,
	'DNAME': 39,
	'SINK': 40,
	'OPT': 41,
	'APL': 42,
	'DS': 43,
	'SSHFP': 44,
	'IPSECKEY': 45,
	'RRSIG': 46,
	'NSEC': 47,
	'DNSKEY': 48,
	'DHCID': 49,
	'NSEC3': 50,
	'NSEC3PARAM': 51,
	'HIP': 55,
	'SPF': 99,

	'TKEY': 249,
	'TSIG': 250,
	'IXFR': 251,
	'AXFR': 252,
	'MAILB': 253,
	'MAILA': 254,
	'*': 255, # ANY
	'TA': 32768,
}

#: Mapping of numeric record identifiers to their text type.
id_to_type = dict((y,x) for (x,y) in type_to_id.items())

#: Mapping of query class names text names to their numeric identifier.
class_to_id = {
	'IN': 1,
	'CS': 2,
	'CH': 3,
	'HS': 4,
	'*': 255, # ANY
}

#: Mapping of numeric identifiers to their corresponding query class name.
id_to_class = dict((y,x) for (x,y) in class_to_id.items())

#: List of opcodes. (Mapping of identifiers to names.)
id_to_operation = (
	'query',
	'inverse',
	'status',
	'notify',
	'update',
)

#: Mapping of operation name to their numeric identifier.
operation_to_id = dict(
	zip(id_to_operation, range(len(id_to_operation)))
)

#: Mapping of error names to codes.
error_to_id = {
	'NONE': 0,
	'FORMAT': 1,
	'SERVER': 2,
	'NAME': 3,
	'NOTIMPLEMENTED': 4,
	'REFUSED': 5,
}

#: Mapping of numeric identifiers to their corresponding query class name.
id_to_error = dict((y,x) for (x,y) in error_to_id.items())
