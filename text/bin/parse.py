"""
# Emit the element tree JSON of the text.
"""
import sys
import importlib
from fault.system import process
from .. import format
from .. import document

formats = {
	'json': ('json', (lambda m,f,a: m.dump(a, f))),
}

def parse(source):
	dt=document.Tree()
	dx = document.Transform(dt)
	fp = format.Parser()
	g = dx.process(fp.parse(source))
	return list(g)

def main(inv:process.Invocation) -> process.Exit:
	format, = inv.argv # Only supports json.
	module_path, process = formats[format]
	module = importlib.import_module(module_path)

	# Parse chapter source.
	ast = parse(sys.stdin.read())

	# Serialize AST.
	process(module, sys.stdout, (('chapter', list(ast)), {}))

	return inv.exit(0)
