"""
# Connect an adapter to the stored security context.
"""
import os
import copy

from ...system import files
from ...system import process

from ...project import system as lsf
from ...project import factory

info = lsf.types.Information(
	identifier = 'http://fault.io/python/security/kprotocol-',
	name = 'kprotocol-',
	authority = 'fault.io',
	contact = "http://fault.io/critical"
)

requirements = '\n'.join([
	'http://fault.io/python/system/extensions.interfaces',
	'http://fault.io/python/security/implementations',
])

formats = {
	'http://if.fault.io/factors/system': [
		('elements', 'c', '2011', 'c'),
		('void', 'h', 'header', 'c'),
		('references', 'sr', 'lines', 'text'),
	],
	'http://if.fault.io/factors/python': [
		('module', 'py', 'psf-v3', 'python'),
		('interface', 'pyi', 'psf-v3', 'python'),
	],
	'http://if.fault.io/factors/meta': [
		('references', 'fr', 'lines', 'text'),
	],
}

pyi = lsf.types.factor@'python.interface'
fr = lsf.types.factor@'meta.references'
sr = lsf.types.factor@'system.references'

module_template = """
	#define ADAPTER_{upper} 1
	#define ADAPTER_TRANSPORT_NEW transport_new_{lower}
	#define ADAPTER_VERIFY SSL_VERIFY_PEER
	#define CONTEXT_LOCATION "{context}"
	#include <kprotocol-openssl.h>
	#include <fault/python/module.h>

	INIT(module, 0, PyDoc_STR("{lower} kprotocol adapter using OpenSSL."))
	{{
		return(init_implementation_data(module));
	}}
"""

def init_product(route, roots):
	pdr = (route/'.product').fs_mkdir()
	(pdr/'ROOTS').set_text_content(' '.join(roots))
	pd = lsf.Product(route)
	pd.roots = [lsf.types.factor@x for x in roots]
	pd.update()
	pd.store()
	return pd

def init_project(product, orientation, interfaces, libraries):
	ctxloc = product ** 2 # Stored Security Context location.
	route = product/orientation
	factor = 'extensions.pki'

	pi = copy.copy(info)
	pi.identifier += orientation
	pi.name += orientation

	srcs = [
		('module.c', module_template.format(
			upper = orientation.upper(),
			lower = orientation,
			context = str(ctxloc),
		)),
	]

	pif = [
		('pki', pyi, "# Empty."),
		('fault', fr, requirements),
		('system.context', sr, '\n'.join(libraries)),
	]
	ext = [
		(factor, 'http://if.fault.io/factors/system.extension', [
			'..system',
			'..fault',
		], srcs),
		('system.include', 'http://if.fault.io/factors/meta.sources', [], [
			('openssl', (files.root@interfaces)),
		]),
	]

	p = factory.Parameters.define(pi, formats, sets=ext, soles=pif)
	factory.instantiate(p, route)

def main(inv:process.Invocation) -> process.Exit:
	target, adapter, implementation, orientation, interfaces, *libs = inv.args

	route = files.Path.from_path(target) / 'if'
	init_project(route/adapter, orientation, interfaces, libs)

	pd = init_product(route/adapter, [orientation])
	return inv.exit(0)
