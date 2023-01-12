"""
# Interface configuration format for binding application network services.

# Provides parsing, serialization, and allocation functions for application service interfaces.
"""
from typing import TypeAlias
from collections.abc import Iterable, Sequence

from . import files
from .kernel import Ports as KPorts
from .network import Endpoint
from .network import select_interfaces as if_select
from .network import service

IContext: TypeAlias = tuple[str, Sequence[str]]
ISpecifications: TypeAlias = Iterable[tuple[IContext, Sequence[Endpoint]]]

def if_structure(if_spec:str, *, type='octets', if_select=if_select) -> ISpecifications:
	"""
	# Parse an interface configuration file.

	# [ Parameters ]
	# /if_spec/
		# The configuration text.

	# [ Returns ]
	# Iterator of pairs associating the protocol section and option set
	# with the endpoints listed in the following indented area.
	"""
	# Iterate over named sections.
	# Indented areas contain associated interfaces.
	for protocolsection in if_spec.split('\n.'):
		if not protocolsection or protocolsection.lstrip()[:1] == '#':
			# Empty or comment.
			continue

		proto, *pconfig = protocolsection.split('\n\t')
		proto, s = proto.split(':', 1) # Protocol
		s = s.strip()
		if s:
			stack = tuple(s.split('/'))
		else:
			stack = ()

		proto = proto.strip('.') # Handle initial section case.
		endpoints:list[Endpoint] = []

		for directive in pconfig:
			directive = directive.strip() # Clean empty lines.
			if directive.startswith('#'):
				continue

			if directive[:1] == '/' or directive[:2] == './':
				# Local
				if directive[:1] != '/':
					directive = directive[2:]
				endpoints.append(Endpoint.from_local(directive))
			else:
				try:
					addr, port = directive.rsplit(':', 1)
				except ValueError:
					addr = directive
					port = None

				if addr[:1].isdigit():
					# IPv4
					endpoints.append(Endpoint.from_ip4((addr, int(port or 0))))
				elif addr[:1] == '[' and addr[-1:] == ']':
					# IPv6 (bracketed)
					endpoints.append(Endpoint.from_ip6((addr[1:-1], int(port or 0))))
				else:
					# Name
					cname, ifaddrs = if_select(proto, type, addr)
					if port is not None:
						endpoints.extend(
							x.replace(port=int(port), transport=0, type=type)
							for x in ifaddrs
						)
					else:
						endpoints.extend(ifaddrs)

		# Pairs for dictionary construction.
		yield ((proto, stack), endpoints)

def if_sequence(if_spec:ISpecifications) -> Iterable[str]:
	"""
	# Serialize the endpoints relative to their protocol and option set.

	# [ Parameters ]
	# /if_spec/
		# The series of protocol identifiers and option sets associated with
		# the sequence of &Endpoint instances.
	"""
	for (proto, stack), endpoints in if_spec:
		sr = '/'.join(stack)
		yield ''.join(['.', proto, ':', sr, '\n'])
		for ep in endpoints:
			if ep.type == 'ip4':
				r = str(ep.address) + ':' + str(ep.port)
			elif ep.type == 'ip6':
				r = '[' + str(ep.address) + ']:' + str(ep.port)
			elif ep.type == 'local':
				r = str(ep.address) + str(ep.port)
			yield ''.join(['\t', r, '\n'])

def if_allocate(if_spec:files.Path, *, encoding='utf-8') -> Sequence[tuple[IContext, KPorts]]:
	"""
	# Read the interfaces configuration file, &if_spec, and &service
	# the identified endpoints keeping the association with
	# the endpoint's context.

	# [ Parameters ]
	# /if_spec/
		# Filesystem path to the interface specification file.

	# [ Returns ]
	# A sequence of pairs where the former value is the protocol and option set and the latter
	# is the &KPorts instance holding the allocated file descriptors.
	"""
	text = if_spec.fs_load().decode(encoding)

	return [
		(p, KPorts([service(x) for x in ep]))
		for p, ep in if_structure(text)
	]
