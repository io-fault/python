from ...internet import host as library
from ...internet import ri

def test_endpoint(test):
	ep = library.realize(ri.parse("https://fault.io"))
	test/ep == library.Reference(('internet-names', 'fault.io', 443, 'https'))

	ep = library.realize(ri.parse("http://fault.io/some/path"))
	test/ep == library.Reference(('internet-names', 'fault.io', 80, 'http'))

	ep = library.realize(ri.parse("https://127.0.0.1"))
	test/ep == library.Endpoint.create_ip4("127.0.0.1", 443)

	ep = library.realize(ri.parse("http://[::1]"))
	test/ep == library.Endpoint.create_ip6("::1", 80)
