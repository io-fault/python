"""
# Instantiate FileSystem Template.

# The sections of the chapter represent the available filesystem trees that can be instantiated.
"""
import os
import sys

from ...system import process
from ...system import files

from . import parse
from .. import document

def pairs(items):
	# Identify the key-value pairs of dictionaries.
	for k, v in document.dictionary_pairs(items):
		if v[0] == 'syntax':
			data = ''.join(document.concatenate(v))
		else:
			data = mapping(v[1])

		yield k, data

def mapping(content):
	return dict(pairs(content))

def transform(tree, section):
	section_content = document.section(tree[1], section)
	if section_content is None:
		raise Exception("section not found " + section)

	root = section_content[1]
	if root[0][0] == 'paragraph':
		abstract = root[0]
		start = root[1][1]
	else:
		abstract = None
		start = root[0][1]

	return mapping(start)

def emit(route, data):
	"""
	# Store a template into the given route.
	"""

	for subpath, content in data.items():
		path = route + subpath.split('/')

		if isinstance(content, (bytes, bytearray, memoryview)):
			(path).fs_init(content)
		elif isinstance(content, str):
			(path).fs_init()
			(path).set_text_content(content)
		else:
			assert isinstance(content, dict)
			(path).fs_mkdir()
			emit(path, content)

def instantiate(target, source, section):
	text = source.get_text_content()
	data = (transform(parse.chapter(text), section))
	target.fs_mkdir()
	emit(target, data)

def main(inv:process.Invocation) -> process.Exit:
	try:
		target, filepath, section, *path = inv.args
	except:
		return inv.exit(os.EX_USAGE)

	route = files.Path.from_path(target)
	if route.fs_type() not in {'void', 'directory'}:
		sys.stderr.write("[!# ERROR: path (%r) must be a directory or void.]\n" %(str(route),))
		return inv.exit(os.EX_NOINPUT)

	sourcepath = files.Path.from_path(filepath)
	if sourcepath.fs_type() in {'void', 'directory'}:
		sys.stderr.write("[!# ERROR: source (%r) does not exist or is a directory.]\n" %(str(sourcepath),))
		return inv.exit(os.EX_NOINPUT)

	instantiate(route, sourcepath, section)

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
