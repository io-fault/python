"""
# HTTP host network daemon.
"""
import os
import functools

from ...vector import recognition

from ...system import process
from ...system.interfaces import if_allocate

from ...kernel import system as ksystem
from ...kernel import core as kcore
from ...kernel import io as kio
from ...kernel import dispatch as kdispatch
from ...kernel import daemon

from ...context import tools

from .. import service

optmap = {
	'-F': ('sequence-append', 'listening-interfaces'),
	'-L': ('field-replace', 'concurrency'),
	'-t': ('field-replace', 'trap-host'),
}

def rewrite_names(hostname, host):
	selected = True
	default = hostname
	aliases = list(host['names'])
	host['names'].clear()
	host['networks'] = set()

	for name in aliases:
		if name[:1] == '[' and name[-1:] == ']':
			name = name[1:-1]
			selected = True

		if name[-1] == '.':
			name = name[:-1]
		else:
			name = name + '.' + hostname

		if name[:1] == '*':
			# Suffix match
			selected = False
			host['networks'].add(name[1:])
		else:
			host['names'].add(name)
			if selected:
				default = name
				selected = False

	host['subject'] = default

def parse_host_config(indentation, level, section):
	"""
	# Parse the contents of a `@host` section.
	"""
	methods = set()
	partitions = {}
	redirects = {}
	headers = []

	# State fields.
	symbol = target = mount_point = None

	for directive in section.split('\n' + (level * indentation)):
		if directive.lstrip()[:1] in {'#', ''}:
			# Comment or empty line.
			continue

		# The initial split producing the hostsegments made this indentation relative.
		# No indentation multiplication is necessary here.
		if directive.startswith(indentation):
			# Indented continuations.
			# Add line content to the existing set or sequence.
			if symbol is None:
				pass
			if symbol == ':Redirect':
				redirects[target] += directive.split()
			elif symbol == ':Allow':
				methods += directive.split()
			elif symbol == ':Partition':
				part = partitions[mount_point]

				n = len(part)
				if n > 2:
					# Extend argument vector.
					part += directive[1:].strip().split(' ') # Trim the leading tab.
				else:
					part += directive.strip().split(None, 2 - n)
					if len(part) > 2:
						# Initialize the now present argument vector.
						part[2:] = part[2].rstrip('\n').split(' ')
			else:
				# Extend previously declared header.
				h, v = headers[-1]
				if v:
					v += b' '
				v += directive.strip().encode('utf-8')
				headers[-1] = (h, v)

			continue
		else:
			if directive[:1] == ':':
				symbol, parameters = directive.strip('\n').split(None, 1)
			else:
				symbol, parameters = directive.strip('\n').split(':', 1) #* Remove empty lines.
				headers.append((
					symbol.strip().encode('utf-8'),
					parameters.strip().encode('utf-8')
				))
				continue

		# New setting.
		if symbol == ':Redirect':
			target, *endpoints = parameters.split()
			redirects[target] = endpoints
		elif symbol == ':Partition':
			mount_point, *remainder = parameters.strip().split(None, 3) #* Path is required.
			if mount_point[-1] != '/':
				mount_point += '/'

			if len(remainder) < 3:
				partitions[mount_point] = remainder
			else:
				partitions[mount_points] = remainder[2:] + remainder[2].rstrip('\n').split(' ')
		elif symbol == ':Allow':
			methods = set(parameters.split())
		else:
			# Unknown directive.
			pass

	return {
		'allowed-methods': methods,
		'partitions': partitions,
		'redirects': redirects,
		'headers': headers,
	}

def host_inherit_context(target, source):
	# Sets, union.
	for x in ('allowed-methods',):
		target[x].update(source[x])

	# Dictionaries, setdefaults.
	# Arguably, redirects could be merged at the value level,
	# but it doesn't seem useful so just setdefault.
	for x in ('partitions', 'redirects'):
		d = source[x]
		y = target[x]
		for k, v in d.items():
			y.setdefault(k, v)

	# Header sequence, prefix.
	for x in ('headers',):
		target[x][:0] = source[x]

def parse_network_config(string, indentation='\t', level=0):
	# http host network
	cfg = {}

	# (context-host, *http-hosts)
	cfg_segments = string.split('\n' + (level * indentation) + '@')

	# Everything before the first "^@host:...\n"
	ctx = parse_host_config(indentation, level, cfg_segments[0])

	hlevel = level + 1
	hprefix = (indentation * hlevel)
	for section in cfg_segments[1:]: # Host declaration.
		if not section or section[:1] == '#':
			continue

		# Separate the first line containing the host and alias set.
		hostspec, section_content = section.split('\n' + hprefix, 1)

		hc = parse_host_config(indentation, hlevel, section_content)

		host, aliases = hostspec.split(':', 1)
		hc['names'] = set(aliases.split())
		hc['subject'] = host

		host_inherit_context(hc, ctx)
		cfg[host] = hc

	return cfg

def load_partitions(items):
	from importlib import import_module

	prefixes = {}

	for mnt, router in items:
		module_name, router_name, *argv = router # Insufficient Partition parameters?
		module = import_module(module_name)
		prefixes[mnt] = getattr(module, router_name), argv

	return prefixes

def create_host(name, config):
	parts = load_partitions(config['partitions'].items())
	h = service.Host(parts)

	rewrite_names(name, config)
	h.h_update_names(name, *config['names'])
	if config['headers']:
		h.h_set_headers(config['headers'])

	if 'allowed-methods' in config:
		h.h_allowed_methods = frozenset(x.encode('utf-8') for x in config['allowed-methods'])

	if config['redirects']:
		for target, origins in config['redirects'].items():
			h.h_set_redirects(target, origins)

	return h

def allocate_network(optdata, kports):
	# Interface -> Connections -> (http) Network
	netcfg = {}
	for configpath in optdata['host-networks']:
		net = parse_network_config(open(configpath).read())
		netcfg.update(net)

	hostset = {
		host: create_host(host, hcfg)
		for host, hcfg in netcfg.items()
	}

	network = service.Network(list(hostset.values()))
	network.http_default_host = optdata['trap-host']

	cxns = kio.Connections(network.net_accept)
	ifs = []
	for p, ep in kports.items():
		i = kio.Interface(cxns.cxn_accept, service.protocols[p[0]])
		i.if_install(ep)
		ifs.append(i)

	ifseq = kcore.Sequenced(ifs) # Does not require sequenced shutdown.

	# Terminated in reverse order.
	return kcore.Sequenced([network, cxns, ifseq])

def integrate(name, args):
	optdata = {
		'listening-interfaces': [],
		'host-networks': [],
		'concurrency': os.environ.get('SERVICE_CONCURRENCY', '1'),
		'trap-host': None,
	}

	optevents = recognition.legacy({}, optmap, args)
	optdata['host-networks'] = recognition.merge(optdata, optevents)

	return optdata

def main(inv:process.Invocation) -> process.Exit:
	optdata = integrate(inv.parameters['system']['name'], inv.argv)
	workers = int(optdata.get('concurrency', 1))

	kports = {}
	for configpath in optdata['listening-interfaces']:
		for p, kp in if_allocate(process.fs_pwd()@configpath):
			if p not in kports:
				kports[p] = kp
			else:
				kports[p] += kp

	alloc = functools.partial(allocate_network, optdata, kports)
	net = alloc()
	if workers:
		net = daemon.ProcessManager(net, alloc, concurrency=workers)

	kprocess = ksystem.dispatch(inv, net, identifier='http-network-daemon')
	ksystem.set_root_process(kprocess)
	ksystem.control()

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
