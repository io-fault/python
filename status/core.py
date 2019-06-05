"""
# The types and forms explicitly defined.
"""

# Designate how the object is stored within a Parameter database.
forms = {
	'v-sequence': '<', # +3
	'v-set': 'V', # +2
	'value': 'v', # +1

	'reference': '&', # 0; value is identifier type, stored type should be consistent.

	'representation': 'r', # -1,
	'r-set': 'R', # -2
	'r-sequence': '^', # -3
}

# Counting upwards, the single character codes mapping to an integer identifier.
form_enumeration_definition = ("^Rr", "&", "vV<")

types = {
	'void': 'v',
	'boolean': 'b',
	'integer': 'i',
	'rational': 'r', # rational numbers, potentially in fraction form, but decimal by default.

	'octets': 'o', # Binary string; sequence of bytes.
	'string': 's', # Sequence of unicode characters.
	'paragraph': 'p', # A string that is intended to be perceived as a sequence of sentences; text.

	# Strings holding Resource Indicators.
	'resource-indicator': 'u', # IRI/URI
	'system-file-path': 'f', # String containing a path to a local file.

	# Time Domains
	'duration': 'm', # Measure of Time
	'timestamp': 't', # ISO string represetation
	'date': 'd', # Gregorian Calendar Date

	'exclude': 'X', # Parameter should be excluded from transmission.

	'identifier': 'I', # A string that is intended to be used to identify a Parameter.
	'event': 'E', # EStruct instance.
	'trace': 'T', # Trace instance.
	'message': 'M', # Message instance.
	'report': 'R', # Report instance.
	'failure': 'F', # Failure instance.
	'parameters': 'P',
}

# Types requiring recursive processing for transmission.
collections = {
	'trace', 'message', 'report', 'failure',
}

type_enumeration_definition = (
	"FRMTEIX", "v", "birospufmtd"
)

# String Representations common primitives.
representation_io = {
	'void': ((lambda x: 'void'), (lambda x: None)),
	'boolean': (
		(lambda x: x.__str__().lower()),
		{'true':True,'false':False}.__getitem__
	),
	'string': (str, str),
	'identifier': (str, str),

	'integer': (int, int.__str__),
	'rational': (float, float.__str__),

	# While inefficient, hex is trivial to implement.
	# Implementations will likely prefer [base64 %s] format.
	'octets': (bytes.fromhex, bytes.hex),
}
