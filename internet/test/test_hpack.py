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

if __name__ == '__main__':
    import sys
    from ...development import libtest
    libtest.execute(sys.modules[__name__])
