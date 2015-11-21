"""
Transform the eclectic text from standard input into
UTF-8 encoded XML that is written to standard output.
"""

def main(src, args):
	from .. import library
	data = src.read()
	encoding = args[0] if args else 'utf-8'

	ctx = library.Context()
	s = library.XML.transform(ctx, '', data, encoding=encoding)

	sys.stdout.buffer.write(b'<chapter xmlns="https://fault.io/xml/eclectic">')
	for x in s:
		sys.stdout.buffer.write(x)
	sys.stdout.buffer.write(b'</chapter>')

if __name__ == '__main__':
	import sys
	main(sys.stdin, sys.argv[1:])
