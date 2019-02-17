from .. import library
from .. import ri

def test_endpoint(test):
	ep = library.realize(ri.parse("https://fault.io"))
	test/ep == library.Reference(('domain', 'fault.io', 443, 'https'))

	ep = library.realize(ri.parse("http://fault.io/some/path"))
	test/ep == library.Reference(('domain', 'fault.io', 80, 'http'))

	ep = library.realize(ri.parse("https://127.0.0.1"))
	test/ep == library.Endpoint.create_ip4("127.0.0.1", 443)

	ep = library.realize(ri.parse("http://[::1]"))
	test/ep == library.Endpoint.create_ip6("::1", 80)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules['__main__'])
