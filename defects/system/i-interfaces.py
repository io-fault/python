"""
# Validate interface configuration and service allocations.
"""
from ...system import files
from ...system import interfaces as module
Endpoint = module.Endpoint
F = module.if_structure
f = module.if_sequence

def test_if_structure_comments(test):
	"""
	# - &module.if_structure
	"""
	test/list(module.if_structure("#c1\n\t#c2\n#c3\n")) == []
	test/list(module.if_structure(".proto:stack\n\t# nothing")) == [(('proto', ('stack',)), [])]

def test_if_structure_ip4(test):
	"""
	# - &module.if_structure
	"""
	i = Endpoint.from_ip4(('1.1.1.1', 80))
	test/list(F(".proto:stack\n\t1.1.1.1:80")) == [(('proto', ('stack',)), [i])]

def test_if_structure_ip6(test):
	"""
	# - &module.if_structure
	"""
	i = Endpoint.from_ip6(('::1', 80))
	test/list(F(".proto:stack\n\t[::1]:80")) == [(('proto', ('stack',)), [i])]

def test_if_structure_local(test):
	"""
	# - &module.if_structure
	"""
	i = Endpoint.from_local('/var/sock/none')
	test/list(F(".proto:stack\n\t/var/sock/none")) == [(('proto', ('stack',)), [i])]

def test_multiple_sections(test):
	"""
	# - &module.if_structure
	# - &module.if_sequence
	"""
	lines = "# Header\n"
	lines += ".P1:\n"
	lines += "\t/socket\n"
	lines += ".P2:\n"
	lines += "\t127.0.0.1:80\n"
	lines += ".P3:\n"
	lines += "\t[::1]:80\n"

	records = [
		(('P1', ()), [Endpoint.from_local('/socket')]),
		(('P2', ()), [Endpoint.from_ip4(('127.0.0.1', 80))]),
		(('P3', ()), [Endpoint.from_ip6(('::1', 80))]),
	]
	test/list(F(lines)) == records
	test/("# Header\n" + ''.join(f(records))) == lines

def test_if_structure_localhost(test):
	"""
	# - &module.if_structure
	"""
	lines = ".http:\n"
	lines += "\tlocalhost\n"
	ip4l = Endpoint.from_ip4(('127.0.0.1', 80))
	ip6l = Endpoint.from_ip6(('::1', 80))

	((proto, stack), ifs), = F(lines)
	has4 = ip4l in ifs
	has6 = ip6l in ifs
	test/(has4 or has6) == True

def test_if_allocate(test):
	"""
	# - &module.if_allocate
	"""
	td = test.exits.enter_context(files.Path.fs_tmpdir())

	lines = ".http:\n"
	lines += "\t127.0.0.1:0\n"
	with (td/'service.if').fs_open('w') as f:
		f.write(lines)

	((proto, stack), ports), = module.if_allocate(td/'service.if')
	test/proto == 'http'
	test/len(ports) == 1
