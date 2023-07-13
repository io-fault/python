"""
# Color formatting for file paths, URIs, and timestamps.
"""
import os

palette = {
	'yellow': 0xffff87,
	'blue': 0x0087ff,
}

route_colors = {
	'filesystem-root': palette['blue'],
	'warning': palette['yellow'],

	'directory': 0x0087ff,
	'relatives': 0xff0000,
	'executable': 0x008700,
	'data': 0xc6c6c6,

	'dot-file': 0x808080,
	'file-not-found': 0xaf0000,

	'link': 0xff0000,
	'device': 0xff5f00,
	'socket': 0xff5f00,
	'pipe': 0xff5f00,

	'path': 0x6e6e6e,
	'path-link': 0x005f87,
	'root-segments': 0x4e4e4e,

	'typed': 0x875faf,
	None: None,
}

def route_is_link(route, islink=os.path.islink):
	try:
		return islink(str(route))
	except OSError:
		return False

def _f_route_path(root, route, _is_link=route_is_link):
	tid = route.identifier

	while route.absolute != root.absolute and tid is not None:

		if tid in {'.', '..'}:
			yield ('path', '/')
			yield ('relatives', tid)
		else:
			if _is_link(route):
				yield ('path', '/')
				yield ('path-link', tid)
			else:
				yield ('path', tid + '/')

		route = route.container
		tid = route.identifier
	else:
		yield ('path', '/')

def f_route_path(root, route):
	l = list(_f_route_path(root, route))
	l.reverse()
	return l

def f_route_identifier(route, *, warning=False):
	path = route.absolute
	if warning:
		t = 'warning'
	else:
		t = route.fs_type()
		rid = route.identifier
		if t == 'data':
			if route.fs_executable():
				t = 'executable'
			elif rid[:1] == ".":
				t = 'dot-file'
		elif t == 'void':
			t = 'file-not-found'

	return [(t, route.identifier)]

def f_route_absolute(route, *, warning=False):
	"""
	# Format the absolute path of the given route.
	"""

	if route.identifier is None:
		# root directory path
		return [('filesystem-root', '/')]

	root = route.container
	return f_route_path(root, route.container) + f_route_identifier(route, warning=warning)

if __name__ == '__main__':
	import sys, itertools
	from ...system import files as sysfiles
	from .. import matrix
	screen = matrix.Screen()
	values = sys.argv[1:]

	rp = screen.terminal_type.normal_render_parameters
	for x in values:
		r = sysfiles.Path.from_path(x)
		phrase = screen.Phrase.from_words(
			itertools.chain.from_iterable(
				rp.apply(textcolor=route_colors[typ]).form(s)
				for typ, s in f_route_absolute(r)
			)
		)
		sys.stderr.buffer.write(b''.join(screen.render(phrase)) + screen.reset_text())
		sys.stderr.write("\n")
