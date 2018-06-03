"""
# Delineate a text file.

# Emits serialized Fragments to standard out of the selected Python module.
"""

import sys
from ...system import library as libsys
from ...routes import library as libroutes
from .. import library as libtxt
from ...xml import library as libxml
from kit.factors import fragments

def main(inv:libsys.Invocation):
	filepath, = inv.args
	src = libroutes.File.from_path(filepath)

	w = sys.stdout.buffer.write
	wl = sys.stdout.buffer.writelines

	w(b'<?xml version="1.0" encoding="utf-8"?>')
	w(b'<factor xmlns="http://fault.io/xml/fragments" ')
	w(b'xmlns:txt="http://if.fault.io/xml/text" xmlns:xlink="')
	w(libxml.namespaces['xlink'].encode('utf-8'))
	w(b'" type="documentation">')
	w(b'<chapter>')
	wl(fragments.source_element(libxml.Serialization(), src))
	w(b'<doc>')
	data = src.load(mode='r')
	s = libtxt.XML.transform('txt:', data, encoding='utf-8')
	wl(s)
	w(b'</doc></chapter></factor>')
	sys.stdout.flush()

	sys.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())


