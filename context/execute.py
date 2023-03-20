"""
# Executable factor index for &fault.system.tool bindings.
"""
import importlib
from .. import __name__ as context_name
from ..system import process

index = {
	'python': context_name + '.system.execute',
	'http-cache': context_name + '.web.bin.cache',
	'test-python-module': context_name + '.test.bin.coherence',
}

def activate(factor, element, interface=None):
	importlib.import_module(factor).extend(lambda x: (index[x], 'main'))

def main(inv:process.Invocation) -> process.Exit:
	import sys
	for item in index.items():
		sys.stdout.write("%s %s\n" % item)
