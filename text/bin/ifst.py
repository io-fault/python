"""
# Instantiate filesystem template.

# The sections of the chapter represent the available filesystem trees that can be instantiated.
"""
import sys
from ...system import library as libsys
from ...routes import library as libroutes
from ...xml import lxml
from ...text import library as libtxt
from ...text import xml as txtxml
from ...system import libfactor

def emit_file(route, elements, context=None):
	element = None

	for element in elements:
		name = element.name

		if name == 'literals':
			lines = [x if x else '' for x in [x.first('text()') for x in element]]
			lines = ('\n'.join(lines).encode('utf-8'))
			route.init('file')
			route.store(lines)
		else:
			pass

def emit(route, elements, context=None):
	element = None

	for element in elements:
		name = element.name

		if name == 'dictionary':
			for e, eid, values in element.select('txt:item', 'txt:key/text()', 'txt:value'):
				lits = list(values.select('txt:literals'))
				if lits:
					emit_file(route/eid, values.select('*'), context=context)
				else:
					emit(route/eid, values.select('*'), context=context)
		else:
			pass

def process(document, route, target):
	element = lxml.Query(document, txtxml.namespaces)
	chapter = element.first('/txt:chapter')

	p = "/txt:chapter/txt:section[@identifier='%s']" %(target[0],)
	section, = element.select(p)
	emit(route, section.select('txt:dictionary'))

def load(import_path, template):
	r = libfactor.selected(libroutes.Import.from_fullname(import_path))
	document = r / (template + '.xml')
	return lxml.readfile(str(document))

def main(inv:libsys.Invocation):
	try:
		route, import_path, template, *path = inv.args
	except:
		return inv.exit(libsys.Exit.exiting_from_bad_usage)

	route = libroutes.File.from_path(route)
	if route.exists() and not route.is_directory():
		sys.stderr.write("! ERROR: path (%r) must be a directory.\n" %(str(route),))
		return inv.exit(libsys.Exit.exiting_from_output_inaccessible)

	doc = load(import_path, template)
	process(doc, route, path)

	return inv.exit(libsys.Exit.exiting_from_success)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())
