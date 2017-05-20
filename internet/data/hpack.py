"""
HPACK data for generating indexes.

https://tools.ietf.org/html/rfc7541

[ Properties ]

/static_table
	The predefined headers and constants.

/huffman_code
	The bit strings representing a character value.
"""

static_table = [
	None,
	":authority",
	(":method", "GET"),
	(":method", "POST"),
	(":path", "/"),
	(":path", "/index.html"),
	(":scheme", "http"),
	(":scheme", "https"),
	(":status", "200"),
	(":status", "204"),
	(":status", "206"),
	(":status", "304"),
	(":status", "400"),
	(":status", "404"),
	(":status", "500"),
	"accept-charset",
	("accept-encoding", "gzip, deflate"),
	"accept-language",
	"accept-ranges",
	"accept",
	"access-control-allow-origin",
	"age",
	"allow",
	"authorization",
	"cache-control",
	"content-disposition",
	"content-encoding",
	"content-language",
	"content-length",
	"content-location",
	"content-range",
	"content-type",
	"cookie",
	"date",
	"etag",
	"expect",
	"expires",
	"from",
	"host",
	"if-match",
	"if-modified-since",
	"if-none-match",
	"if-range",
	"if-unmodified-since",
	"last-modified",
	"link",
	"location",
	"max-forwards",
	"proxy-authenticate",
	"proxy-authorization",
	"range",
	"referer",
	"refresh",
	"retry-after",
	"server",
	"set-cookie",
	"strict-transport-security",
	"transfer-encoding",
	"user-agent",
	"vary",
	"via",
	"www-authenticate",
]

huffman_code = [
	'11111111' '11000',
	'11111111' '11111111' '1011000',
	'11111111' '11111111' '11111110' '0010',
	'11111111' '11111111' '11111110' '0011',
	'11111111' '11111111' '11111110' '0100',
	'11111111' '11111111' '11111110' '0101',
	'11111111' '11111111' '11111110' '0110',
	'11111111' '11111111' '11111110' '0111',
	'11111111' '11111111' '11111110' '1000',
	'11111111' '11111111' '11101010',
	'11111111' '11111111' '11111111' '111100',
	'11111111' '11111111' '11111110' '1001',
	'11111111' '11111111' '11111110' '1010',
	'11111111' '11111111' '11111111' '111101',
	'11111111' '11111111' '11111110' '1011',
	'11111111' '11111111' '11111110' '1100',
	'11111111' '11111111' '11111110' '1101',
	'11111111' '11111111' '11111110' '1110',
	'11111111' '11111111' '11111110' '1111',
	'11111111' '11111111' '11111111' '0000',
	'11111111' '11111111' '11111111' '0001',
	'11111111' '11111111' '11111111' '0010',
	'11111111' '11111111' '11111111' '111110',
	'11111111' '11111111' '11111111' '0011',
	'11111111' '11111111' '11111111' '0100',
	'11111111' '11111111' '11111111' '0101',
	'11111111' '11111111' '11111111' '0110',
	'11111111' '11111111' '11111111' '0111',
	'11111111' '11111111' '11111111' '1000',
	'11111111' '11111111' '11111111' '1001',
	'11111111' '11111111' '11111111' '1010',
	'11111111' '11111111' '11111111' '1011',
	'010100',
	'11111110' '00',
	'11111110' '01',
	'11111111' '1010',
	'11111111' '11001',
	'010101',
	'11111000',
	'11111111' '010',
	'11111110' '10',
	'11111110' '11',
	'11111001',
	'11111111' '011',
	'11111010',
	'010110',
	'010111',
	'011000',
	'00000',
	'00001',
	'00010',
	'011001',
	'011010',
	'011011',
	'011100',
	'011101',
	'011110',
	'011111',
	'1011100',
	'11111011',
	'11111111' '1111100',
	'100000',
	'11111111' '1011',
	'11111111' '00',
	'11111111' '11010',
	'100001',
	'1011101',
	'1011110',
	'1011111',
	'1100000',
	'1100001',
	'1100010',
	'1100011',
	'1100100',
	'1100101',
	'1100110',
	'1100111',
	'1101000',
	'1101001',
	'1101010',
	'1101011',
	'1101100',
	'1101101',
	'1101110',
	'1101111',
	'1110000',
	'1110001',
	'1110010',
	'11111100',
	'1110011',
	'11111101',
	'11111111' '11011',
	'11111111' '11111110' '000',
	'11111111' '11100',
	'11111111' '111100',
	'100010',
	'11111111' '1111101',
	'00011',
	'100011',
	'00100',
	'100100',
	'00101',
	'100101',
	'100110',
	'100111',
	'00110',
	'1110100',
	'1110101',
	'101000',
	'101001',
	'101010',
	'00111',
	'101011',
	'1110110',
	'101100',
	'01000',
	'01001',
	'101101',
	'1110111',
	'1111000',
	'1111001',
	'1111010',
	'1111011',
	'11111111' '1111110',
	'11111111' '100',
	'11111111' '111101',
	'11111111' '11101',
	'11111111' '11111111' '11111111' '1100',
	'11111111' '11111110' '0110',
	'11111111' '11111111' '010010',
	'11111111' '11111110' '0111',
	'11111111' '11111110' '1000',
	'11111111' '11111111' '010011',
	'11111111' '11111111' '010100',
	'11111111' '11111111' '010101',
	'11111111' '11111111' '1011001',
	'11111111' '11111111' '010110',
	'11111111' '11111111' '1011010',
	'11111111' '11111111' '1011011',
	'11111111' '11111111' '1011100',
	'11111111' '11111111' '1011101',
	'11111111' '11111111' '1011110',
	'11111111' '11111111' '11101011',
	'11111111' '11111111' '1011111',
	'11111111' '11111111' '11101100',
	'11111111' '11111111' '11101101',
	'11111111' '11111111' '010111',
	'11111111' '11111111' '1100000',
	'11111111' '11111111' '11101110',
	'11111111' '11111111' '1100001',
	'11111111' '11111111' '1100010',
	'11111111' '11111111' '1100011',
	'11111111' '11111111' '1100100',
	'11111111' '11111110' '11100',
	'11111111' '11111111' '011000',
	'11111111' '11111111' '1100101',
	'11111111' '11111111' '011001',
	'11111111' '11111111' '1100110',
	'11111111' '11111111' '1100111',
	'11111111' '11111111' '11101111',
	'11111111' '11111111' '011010',
	'11111111' '11111110' '11101',
	'11111111' '11111110' '1001',
	'11111111' '11111111' '011011',
	'11111111' '11111111' '011100',
	'11111111' '11111111' '1101000',
	'11111111' '11111111' '1101001',
	'11111111' '11111110' '11110',
	'11111111' '11111111' '1101010',
	'11111111' '11111111' '011101',
	'11111111' '11111111' '011110',
	'11111111' '11111111' '11110000',
	'11111111' '11111110' '11111',
	'11111111' '11111111' '011111',
	'11111111' '11111111' '1101011',
	'11111111' '11111111' '1101100',
	'11111111' '11111111' '00000',
	'11111111' '11111111' '00001',
	'11111111' '11111111' '100000',
	'11111111' '11111111' '00010',
	'11111111' '11111111' '1101101',
	'11111111' '11111111' '100001',
	'11111111' '11111111' '1101110',
	'11111111' '11111111' '1101111',
	'11111111' '11111110' '1010',
	'11111111' '11111111' '100010',
	'11111111' '11111111' '100011',
	'11111111' '11111111' '100100',
	'11111111' '11111111' '1110000',
	'11111111' '11111111' '100101',
	'11111111' '11111111' '100110',
	'11111111' '11111111' '1110001',
	'11111111' '11111111' '11111000' '00',
	'11111111' '11111111' '11111000' '01',
	'11111111' '11111110' '1011',
	'11111111' '11111110' '001',
	'11111111' '11111111' '100111',
	'11111111' '11111111' '1110010',
	'11111111' '11111111' '101000',
	'11111111' '11111111' '11110110' '0',
	'11111111' '11111111' '11111000' '10',
	'11111111' '11111111' '11111000' '11',
	'11111111' '11111111' '11111001' '00',
	'11111111' '11111111' '11111011' '110',
	'11111111' '11111111' '11111011' '111',
	'11111111' '11111111' '11111001' '01',
	'11111111' '11111111' '11110001',
	'11111111' '11111111' '11110110' '1',
	'11111111' '11111110' '010',
	'11111111' '11111111' '00011',
	'11111111' '11111111' '11111001' '10',
	'11111111' '11111111' '11111100' '000',
	'11111111' '11111111' '11111100' '001',
	'11111111' '11111111' '11111001' '11',
	'11111111' '11111111' '11111100' '010',
	'11111111' '11111111' '11110010',
	'11111111' '11111111' '00100',
	'11111111' '11111111' '00101',
	'11111111' '11111111' '11111010' '00',
	'11111111' '11111111' '11111010' '01',
	'11111111' '11111111' '11111111' '1101',
	'11111111' '11111111' '11111100' '011',
	'11111111' '11111111' '11111100' '100',
	'11111111' '11111111' '11111100' '101',
	'11111111' '11111110' '1100',
	'11111111' '11111111' '11110011',
	'11111111' '11111110' '1101',
	'11111111' '11111111' '00110',
	'11111111' '11111111' '101001',
	'11111111' '11111111' '00111',
	'11111111' '11111111' '01000',
	'11111111' '11111111' '1110011',
	'11111111' '11111111' '101010',
	'11111111' '11111111' '101011',
	'11111111' '11111111' '11110111' '0',
	'11111111' '11111111' '11110111' '1',
	'11111111' '11111111' '11110100',
	'11111111' '11111111' '11110101',
	'11111111' '11111111' '11111010' '10',
	'11111111' '11111111' '1110100',
	'11111111' '11111111' '11111010' '11',
	'11111111' '11111111' '11111100' '110',
	'11111111' '11111111' '11111011' '00',
	'11111111' '11111111' '11111011' '01',
	'11111111' '11111111' '11111100' '111',
	'11111111' '11111111' '11111101' '000',
	'11111111' '11111111' '11111101' '001',
	'11111111' '11111111' '11111101' '010',
	'11111111' '11111111' '11111101' '011',
	'11111111' '11111111' '11111111' '1110',
	'11111111' '11111111' '11111101' '100',
	'11111111' '11111111' '11111101' '101',
	'11111111' '11111111' '11111101' '110',
	'11111111' '11111111' '11111101' '111',
	'11111111' '11111111' '11111110' '000',
	'11111111' '11111111' '11111011' '10',
	'11111111' '11111111' '11111111' '111111', # EOS
]

huffman_reverse_index = {
	huffman_code[i]: i for i in range(len(huffman_code))
}

h_start = min(map(len, huffman_code))
h_stop = max(map(len, huffman_code)) + 1
