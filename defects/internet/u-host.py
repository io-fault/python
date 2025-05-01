from ...internet import host as module
from ...internet import ri

def test_endpoint(test):
	ep = module.realize(ri.parse("https://fault.io"))
	test/ep == module.Reference(('internet-names', 'fault.io', 443, 'https'))

	ep = module.realize(ri.parse("http://fault.io/some/path"))
	test/ep == module.Reference(('internet-names', 'fault.io', 80, 'http'))

	ep = module.realize(ri.parse("https://127.0.0.1"))
	test/ep == module.Endpoint.create_ip4("127.0.0.1", 443)

	ep = module.realize(ri.parse("http://[::1]"))
	test/ep == module.Endpoint.create_ip6("::1", 80)
