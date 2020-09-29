"""
# Read the syntax from a dictionary entry inside a selected sections.
"""
import os
import sys

from ...system import process
from ...system import files

from .. import document
from . import parse

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
	section_content = document.section(tree, section)
	if section_content is None:
		raise Exception("section not found " + section)

	root = section_content[1]
	x = 0
	for x in range(len(root)):
		if root[0][0] == 'dictionary':
			break

	start = root[x][1]

	return mapping(start)

def structure(source, section):
	text = source.get_text_content()
	data = (transform(parse.chapter(text), section))
	return data

def main(inv:process.Invocation) -> process.Exit:
	try:
		filepath, section, *paths = inv.args
	except:
		return inv.exit(os.EX_USAGE)

	sourcepath = files.Path.from_path(filepath)
	if sourcepath.fs_type() in {'void', 'directory'}:
		sys.stderr.write("[!# ERROR: source (%r) does not exist or is a directory]\n" %(str(sourcepath),))
		return inv.exit(os.EX_NOINPUT)

	data = structure(sourcepath, section)
	if not paths:
		paths = data.keys()

	for p in paths:
		sys.stdout.write(data[p])

	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
