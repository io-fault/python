"""
# Read the syntax from a dictionary entry inside a selected sections.
"""
import sys

from ...system import process
from ...system import files

from ...text import library as libtext

def pairs(items):
	# Identify the key-value pairs of dictionaries.
	for k, v in libtext.document.dictionary_pairs(items):
		if v[0] == 'syntax':
			data = ''.join(libtext.document.concatenate(v))
		else:
			data = mapping(v[1])

		yield k, data

def mapping(content):
	return dict(pairs(content))

def transform(tree, section):
	section_content = libtext.document.section(tree, section)
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

def structure(source, section):
	text = source.get_text_content()
	data = (transform(libtext.parse(text), section))
	return data

def main(inv:process.Invocation) -> process.Exit:
	try:
		filepath, section, *paths = inv.args
	except:
		return inv.exit(process.Exit.exiting_from_bad_usage)

	sourcepath = files.Path.from_path(filepath)
	if not sourcepath.exists() or sourcepath.is_directory():
		sys.stderr.write("! ERROR: source (%r) does not exist or is a directory.\n" %(str(sourcepath),))
		return inv.exit(process.Exit.exiting_from_input_inaccessible)

	data = structure(sourcepath, section)
	for p in paths:
		sys.stdout.write(data[p])

	return inv.exit(process.Exit.exiting_from_success)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
