from .. import libri

def cmbx(t):
	'Yield a list of combinations using a mask'
	tl = len(t)
	return [
		[x & m and t[x-1] or '' for x in range(1, tl + 1)]
		for m in range(1, (2 ** tl) + 1)
	]

expectation_samples = (
	(
		'',
		('none', None, None, None, None, None),
		{
			'type': 'none',
			'scheme': None,
		}
	),

	# cover the amorphous type.
	# indicates a 'none' scheme, but where the remaining
	(
		'x@fault.io:80',
		('amorphous', None, 'x@fault.io:80', None, None, None),
		{
			'type': 'amorphous',
			'scheme' : None,
			'host': 'fault.io',
			'port': '80',
			'user': 'x',
		}
	),

	(
		'fault.io:80',
		('amorphous', None, 'fault.io:80', None, None, None),
		{
			'type': 'amorphous',
			'scheme' : None,
			'host': 'fault.io',
			'port': '80',
		}
	),

	(
		'/path1/',
		('none', None, None, 'path1/', None, None),
		{
			'type': 'none',
			'scheme' : None,
			'path' : ['path1',''],
		}
	),

	(
		'host',
		('none', None, 'host', None, None, None),
		{
			'type' : 'none',
			'scheme': None,
			'host' : 'host',
		}
	),

	(
		'http://host',
		('authority', 'http', 'host', None, None, None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
		}
	),

	# arbitrary scheme support
	(
		'x-un+known://host',
		('authority', 'x-un+known', 'host', None, None, None),
		{
			'type': 'authority',
			'scheme' : 'x-un+known',
			'host' : 'host',
		}
	),

	(
		'http://host/',
		('authority', 'http', 'host', '', None, None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : [],
		}
	),

	(
		'http://host/path1',
		('authority', 'http', 'host', 'path1', None, None),
		{
			'type' : 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1'],
		}
	),

	(
		'mailto:',
		('absolute', 'mailto', None, None, None, None),
		{
			'type': 'absolute',
			'scheme' : 'mailto',
		}
	),

	(
		'mailto:x@fault.io',
		('absolute', 'mailto', 'x@fault.io', None, None, None),
		{
			'type': 'absolute',
			'scheme' : 'mailto',
			'user': 'x',
			'host': 'fault.io',
		}
	),

	(
		'mailto:x@fault.io?foo=bar',
		('absolute', 'mailto', 'x@fault.io', None, 'foo=bar', None),
		{
			'type': 'absolute',
			'scheme' : 'mailto',
			'user': 'x',
			'host': 'fault.io',
			'query': [
				('foo', 'bar')
			]
		}
	),

	(
		'//host:/path1/',
		('relative', None, 'host:', 'path1/', None, None),
		{
			'type': 'relative',
			'scheme' : None,
			'host' : 'host',
			'port' : '',
			'path' : ['path1',''],
		}
	),

	(
		'//host/path1/',
		('relative', None, 'host', 'path1/', None, None),
		{
			'type': 'relative',
			'scheme' : None,
			'host' : 'host',
			'path' : ['path1',''],
		}
	),

	(
		'http://host/path1/',
		('authority', 'http', 'host', 'path1/', None, None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1',''],
		}
	),
	(
		'http://host/path1/path2',
		('authority', 'http', 'host', 'path1/path2', None, None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1','path2'],
		}
	),
	(
		'http://host/path1/path2?k=v&k2=v2',
		('authority', 'http', 'host', 'path1/path2', 'k=v&k2=v2', None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1','path2'],
			'query' : [('k', 'v'), ('k2', 'v2')],
		}
	),
	(
		'http://host/path1/path2?k=v',
		('authority', 'http', 'host', 'path1/path2', 'k=v', None),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
		}
	),
	(
		'http://host/path1/path2?k=v#',
		('authority', 'http', 'host', 'path1/path2', 'k=v', ''),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
			'fragment' : '',
		}
	),
	(
		'http://host/path1/path2?k=v#fragment',
		('authority', 'http', 'host', 'path1/path2', 'k=v', 'fragment'),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
			'fragment' : 'fragment',
		}
	),
	(
		'http://host:port/path1/path2?k=v#fragment',
		('authority', 'http', 'host:port', 'path1/path2', 'k=v', 'fragment'),
		{
			'type': 'authority',
			'scheme' : 'http',
			'host' : 'host',
			'port' : 'port',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
			'fragment' : 'fragment',
		}
	),
	(
		'http://user@host:port/path1/path2?k=v#fragment',
		('authority', 'http', 'user@host:port', 'path1/path2', 'k=v', 'fragment'),
		{
			'type': 'authority',
			'scheme' : 'http',
			'user' : 'user',
			'host' : 'host',
			'port' : 'port',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
			'fragment' : 'fragment',
		}
	),
	(
		'http://user:pass@host:port/path1/path2?k=v#fragment',
		('authority', 'http', 'user:pass@host:port', 'path1/path2', 'k=v', 'fragment'),
		{
			'type': 'authority',
			'scheme' : 'http',
			'user' : 'user',
			'password' : 'pass',
			'host' : 'host',
			'port' : 'port',
			'path' : ['path1','path2'],
			'query' : [('k', 'v')],
			'fragment' : 'fragment',
		}
	),
	(
		'ftp://user:pass@host:port/pa%2Fth1/path2?#',
		('authority', 'ftp', 'user:pass@host:port', 'pa%2Fth1/path2', '', ''),
		{
			'type': 'authority',
			'scheme' : 'ftp',
			'user' : 'user',
			'password' : 'pass',
			'host' : 'host',
			'port' : 'port',
			'path' : ['pa/th1','path2'],
			'query' : [],
			'fragment' : '',
		}
	),
	(
		'ftp://us%40er:pa:ss@host:port/pa%2Fth1/path2?#',
		('authority', 'ftp', 'us%40er:pa:ss@host:port', 'pa%2Fth1/path2', '', ''),
		{
			'type': 'authority',
			'scheme' : 'ftp',
			'user' : 'us@er',
			'password' : 'pa:ss',
			'host' : 'host',
			'port' : 'port',
			'path' : ['pa/th1','path2'],
			'query' : [],
			'fragment' : '',
		}
	),
	(
		'ftp://us%40er:pa:ss@host:port/pa%2Fth1/path2?%23=%23#',
		('authority', 'ftp', 'us%40er:pa:ss@host:port', 'pa%2Fth1/path2', '%23=%23', ''),
		{
			'type': 'authority',
			'scheme' : 'ftp',
			'user' : 'us@er',
			'password' : 'pa:ss',
			'host' : 'host',
			'port' : 'port',
			'path' : ['pa/th1','path2'],
			'query' : [('#', '#')],
			'fragment' : '',
		}
	),
)

sample_join_netlocs = (
	'sample.com',
	'host',
	'host:port',
	'host:8080',
	'@host',
	'%40@',
	'%40:@host',
	'user@',
	'user:@',
	'user:pass@',
	':@host',
	':@host:8080',
	'user:@host:8080',
	'user:@[]:8080',
	'user:@[::1]:8080',
	'user:@[text]:8080',
	'user:@[:8080',
	'user:@[fe80::1]:8080',
	'user:pass@host:8080',
	'user:pass@host',
)

sample_split_netlocs = (
	('user', 'pass', 'host', 'port'),
	('@', ':', 'host', 'port'),
	('@user', 'pass:', 'host', 'port'),
	('@user', 'pass:', 'host', ''),
	('@user', 'pass:', '', ''),
	('user', '@', 'host.com', ''),
	('user', '@', 'å.com', '8080'),
	('user', '', 'x--na.com', '8080'),
	('', '', 'x--na.com', '8080'),
	('', '', '', '8080'),
	('', '', '', ''),
)

sample_join_paths = (
	None,
	'',
	'/',
	'///',
	'/path',
	'/path/path2',
	'/path/path2/',
	'/path2',
	'/åß∂',
	'/åß∂/',
	'/åß∂//',
	'/element1/element2/element3',
)

sample_schemes = (
	('authority', 'http'),
	('relative', None),
	('absolute', 'https'),
)

sample_users = (
	'',
	':',
	'@',
	'user@',
	'user',
	'jæms',
)

sample_passwords = [
	'',
	':',
	'@',
	'æçèêí',
]

sample_hosts = [
	'',
	'[::1]',
	#'[::1', Fail case. Can't use this host and correctly identify the port.
	#'::1]', Fail case. Can't use this host and correctly identify the port.
	'remotehost.tld',
]

sample_ports = [
	'',
	'80',
	'foo',
	':',
]

sample_paths = (
	[],
	# [''], Fail case. Can't represent this structure consistently.
	['', ''],
	['/',],
	['path/'],
	['path','/path2'],
)

sample_queries = (
	[],
	# [('', None)], Fail case. Can't represent this structure consistently.
	[('key', None)],
	[('key', 'val'), ('key', None), ('?', '=')],
	[('=', '=')],
)

sample_fragments = (
	'',
	'#',
	'\x05',
	'%05',
)

def samples():
	for s in sample_schemes:
		for u in sample_users:
			for p in sample_passwords:
				for h in sample_hosts:
					for pt in sample_ports:
						for path in sample_paths:
							for q in sample_queries:
								for f in sample_fragments:
									r = {
										'type' : s[0],
										'scheme' : s[1],
										'user' : u,
										'password' : p,
										'host' : h,
										'port' : pt,
										'path' : path,
										'query' : q,
										'fragment' : f,
									}
									yield r

def test_expectations(test):
	for x in expectation_samples:
		text, split, parsed = x

		text_split = libri.split(text)
		text_parsed = libri.parse(text)

		split_join = libri.join(split)
		split_structure = libri.structure(split)

		parsed_construct = libri.construct(parsed)
		parsed_serialize = libri.serialize(parsed)

		test/text_parsed == parsed
		test/parsed_serialize == text
		test/parsed_construct == split
		test/split_join == text
		test/split_structure == parsed
		test/text_split == split

def test_split_join_netloc(test):
	for x in sample_join_netlocs:
		sn = libri.split_netloc(x)
		usn = libri.join_netloc(sn)
		test/usn == x

def test_join_split_netloc(test):
	for xx in sample_split_netlocs:
		for x in cmbx(xx):
			x = tuple(x)
			un = libri.join_netloc(x)
			sn = tuple(libri.split_netloc(un))
			test/sn == x

def test_split_join_path(test):
	for x in sample_join_paths:
		s = libri.split_path(x)
		us = libri.join_path(s)
		test/us == x

def test_join_split_path(test):
	for x in sample_paths:
		us = libri.join_path(x)
		s = libri.split_path(us)
		test/s == x

def test_combinations(test, S = libri.serialize, P = libri.parse):
	for x in samples():
		s = S(x); p = P(s)
		if p != x:
			test.fail("%r -> %r != %r" %(x, s, p))

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules['__name__'])
