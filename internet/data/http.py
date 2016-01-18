VERSION10 = b'HTTP/1.0'
VERSION11 = b'HTTP/1.1'

VERSIONS = frozenset((VERSION10, VERSION11))

#: Carriage Return, Line Feed (Separates Headers)
CRLF = b'\r\n'

#: Space
SP = b' '

#: Header Field Separator
HFS = b': '

classes = dict(
	CLASS_INFORMATIONAL = b'1',
	CLASS_SUCCESS = b'2',
	CLASS_REDIRECTION = b'3',
	CLASS_CLIENT_ERROR = b'4',
	CLASS_SERVER_ERROR = b'5',
)
class_names = (
	None,
	'INFORMATIONAL',
	'SUCCES',
	'REDIRECTION',
	'CLIENT_ERROR',
	'SERVER_ERROR',
)

##
# HTTP Data
##
# 1xx: Informational
#  Request received, continuing process
codes = dict(
	CONTINUE = b'100',
	SWITCHING_PROTOCOL = b'101',

##
# 2xx: Success
#  The action was successfully received, understood, and accepted
	OK = b'200',
	CREATED = b'201',
	ACCEPTED = b'202',
	NON_AUTHORITATIVE = b'203',
	NO_CONTENT = b'204',
	RESET_CONTEXT = b'205',
	PARTIAL_CONTENT = b'206',
	MULTI_STATUS = b'207',
	ALREADY_REPORTED = b'208',
	IM_USED = b'226',

##
# 3xx: Redirection
#  Further action must be taken in order to complete the request
	MULTIPLE_CHOICES = b'300',
	MOVED_PERMANENTLY = b'301',
	FOUND = b'302',
	SEE_OTHER = b'303',
	NOT_MODIFIED = b'304',
	USE_PROXY = b'305',
	TEMPORARY_REDIRECT = b'307',

##
# 4xx: Client Error
#  The request contains bad syntax or cannot be fulfilled
	BAD_REQUEST = b'400',
	UNAUTHORIZED = b'401',
	PAYMENT_REQUIRED = b'402',
	FORBIDDEN = b'403',
	NOT_FOUND = b'404',
	METHOD_NOT_ALLOWED = b'405',
	NOT_ACCEPTABLE = b'406',
	PROXY_AUTHENTICATION_REQUIRED = b'407',
	REQUEST_TIMEOUT = b'408',
	CONFLICT = b'409',
	GONE = b'410',
	LENGTH_REQUIRED = b'411',
	PRECONDITION_FAILED = b'412',
	REQUEST_ENTITY_TOO_LARGE = b'413',
	REQUEST_URI_TOO_LARGE = b'414',
	UNSUPPORTED_MEDIA_TYPE = b'415',
	REQUESTED_RANGE_NOT_SATISFIABLE = b'416',
	EXPECTATION_FAILED = b'417',
	UNPROCESSABLE_ENTITY = b'422',
	LOCKED = b'423',
	FAILED_DEPENDENCY = b'424',
	UPGRADE_REQUIRED = b'426',
	PRECONDITION_REQUIRED = b'428',
	TOO_MANY_REQUESTS = b'429',
	REQUEST_HEADER_FIELDS_TOO_LARGE = b'431',

##
# 5xx: Server Error
#  The server failed to fulfill an apparently valid request
	INTERNAL_SERVER_ERROR = b'500',
	NOT_IMPLEMENTED = b'501',
	BAD_GATEWAY = b'502',
	SERVICE_UNAVAILABLE = b'503',
	GATEWAY_TIMEOUT = b'504',
	UNSUPPORTED_HTTP_VERSION = b'505',
	INSUFFICIENT_STORAGE = b'507',
	LOOP_DETECTED = b'508',
	NOT_EXTENDED = b'510',
	NETWORK_AUTHENTICATION_REQUIRED = b'511',
)
code_to_names = {v:k for k,v in codes.items()}
