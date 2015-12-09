"""
Transform the eclectic text from standard input into a token stream.
"""

def main(src, args):
	from .. import core
	p = core.Parser()
	for x in p.tokenize(src.readlines()):
		sys.stdout.write(repr(x)+'\n')

if __name__ == '__main__':
	import sys
	main(sys.stdin, sys.argv[1:])
