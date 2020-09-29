"""
# Parse the text file from standard input and serialize the element tree into standard output.

# The format of the output is designated using the first argument: print, json.
"""
import sys
import importlib

from ...system import process

from .. import format
from .. import document

formats = {
	'json': ('json', (lambda m,f,a: m.dump(a, f))),
	'print': ('pprint', (lambda m,f,a: f.write(m.pformat(a)))),
}

def chapter(source):
	dt=document.Tree()
	dx = document.Transform(dt)
	fp = format.Parser()
	return dx.process(fp.parse(source))

def main(inv:process.Invocation) -> process.Exit:
	format, = inv.argv # 'json' or 'print'
	module_path, process = formats[format]
	module = importlib.import_module(module_path, __package__)

	# Parse chapter source.
	ast = chapter(sys.stdin.read())

	# Serialize AST.
	process(module, sys.stdout, ast)

	return inv.exit(0)
