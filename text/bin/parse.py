"""
# Parse the text file from standard input and serialize the element tree into standard output.

# The format of the output is designated using the first argument: print, json.
"""
import sys
import importlib

from ...system import process
from .. import io as txt

formats = {
	'json': ('json', (lambda m,f,a: m.dump(a, f))),
	'print': ('pprint', (lambda m,f,a: f.write(m.pformat(a)))),
}

def main(inv:process.Invocation) -> process.Exit:
	format, = inv.argv # 'json' or 'print'
	module_path, process = formats[format]
	module = importlib.import_module(module_path, __package__)

	# Parse chapter source.
	chapter = txt.structure_chapter_text(sys.stdin.read())

	# Serialize AST.
	process(module, sys.stdout, chapter)

	return inv.exit(0)
