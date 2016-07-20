"""
Transform the fault.text from standard input into UTF-8 encoded XML that is written to standard output.
The one optional argument selects the encoding of the XML output.
"""

def main(src, args):
	from .. import library
	data = src.read()
	encoding = args[0] if args else 'utf-8'

	s = library.XML.transform('', data, encoding=encoding)

	tag_open = '<chapter xmlns="https://fault.io/xml/text">'.encode(encoding)
	sys.stdout.buffer.write(tag_open)
	sys.stdout.buffer.writelines(s)
	sys.stdout.buffer.write('</chapter>'.encode(encoding))

if __name__ == '__main__':
	import sys
	main(sys.stdin, sys.argv[1:])
