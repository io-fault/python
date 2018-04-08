from .. import hpack as module

samples = [
    b'www.example.com',
    b'www.com',
    b'www.',
    b'no-cache',
    b'af23958cbde0293cd099affff',
    b'\x00\x00\x00\x00',
    b'\xff\xff\xff\xff',
    bytes(range(256)),
]

def test_huffman_coding(test):
    for x in samples:
        coded = module.huffman_encode(x)
        test/x == module.huffman_decode(coded)

def test_huffman_samples(test):
	"""
	# Tests comprised of data from examples in
	# &<http://httpwg.org/specs/rfc7541.html>
	"""
	test/module.huffman_decode(b'\xae\xc3\x77\x1a\x4b') == b'private'
	test/module.huffman_encode(b'private') == b'\xae\xc3\x77\x1a\x4b'

	i = b''.join([
		b'\xd0\x7a\xbe\x94\x10',
		b'\x54\xd4\x44\xa8\x20',
		b'\x05\x95\x04\x0b\x81',
		b'\x66\xe0\x82\xa6\x2d',
		b'\x1b\xff'
	])
	out = b'Mon, 21 Oct 2013 20:13:21 GMT'
	test/module.huffman_decode(i) == out
	test/module.huffman_encode(out) == i

	j = b''.join([
		b'\x9d\x29\xad\x17',
		b'\x18\x63\xc7\x8f',
		b'\x0b\x97\xc8\xe9',
		b'\xae\x82\xae\x43',
		b'\xd3'
	])
	out = b'https://www.example.com'
	test/module.huffman_decode(j) == out
	test/module.huffman_encode(out) == j

if __name__ == '__main__':
    import sys
    from ...test import library as libtest
    libtest.execute(sys.modules[__name__])
