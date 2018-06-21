"""
# Instantiate FileSystem Template.

# The sections of the chapter represent the available filesystem trees that can be instantiated.
"""
import sys
from ...system import library as libsys
from ...routes import library as libroutes
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

def emit(route, data):
	"""
	# Store a template into the given route.
	"""

	for filename, content in data.items():
		if isinstance(content, (bytes, bytearray, memoryview)):
			(route/filename).store(content)
		elif isinstance(content, str):
			(route/filename).set_text_content(content)
		else:
			assert isinstance(content, dict)
			(route/filename).init('directory')
			emit(route/filename, content)

def instantiate(target, source, section):
	text = source.get_text_content()
	data = (transform(libtext.parse(text), section))
	if not target.exists():
		target.init('directory')

	emit(target, data)

def main(inv:libsys.Invocation):
	try:
		target, filepath, section, *path = inv.args
	except:
		return inv.exit(libsys.Exit.exiting_from_bad_usage)

	route = libroutes.File.from_path(target)
	if route.exists() and not route.is_directory():
		sys.stderr.write("! ERROR: path (%r) must be a directory.\n" %(str(route),))
		return inv.exit(libsys.Exit.exiting_from_output_inaccessible)

	sourcepath = libroutes.File.from_path(filepath)
	if not sourcepath.exists() or sourcepath.is_directory():
		sys.stderr.write("! ERROR: source (%r) does not exist or is a directory.\n" %(str(sourcepath),))
		return inv.exit(libsys.Exit.exiting_from_input_inaccessible)

	instantiate(route, sourcepath, section)

	return inv.exit(libsys.Exit.exiting_from_success)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())
