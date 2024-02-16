"""
# Color formatting for file paths, URIs, and timestamps.
"""
import os

from .. import palette

route_colors = {
	'filesystem-root': 0xfafafa,
	'warning': palette.colors['yellow'],

	'directory': palette.colors['blue'],
	'relatives': 0xff0000,
	'executable': palette.colors['green'],
	'data': 0xc6c6c6,

	'dot-file': palette.colors['gray'],
	'file-not-found': palette.colors['red'],

	'link': palette.colors['violet'],
	'device': 0xff5f00,
	'socket': 0xff5f00,
	'pipe': 0xff5f00,

	'path-separator': palette.colors['background-adjacent'],
	'path-directory': palette.colors['gray'],
	'path-link': palette.colors['violet'],

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
			yield ('path-separator', '/')
			yield ('relatives', tid)
		else:
			if _is_link(route):
				yield ('path-separator', '/')
				yield ('path-link', tid)
			else:
				yield ('path-separator', '/')
				pd, = f_route_identifier(route)
				if pd[0] == 'directory':
					yield ('path-directory', tid)
				else:
					yield pd

		route = route.container
		tid = route.identifier
	else:
		yield ('path-separator', '/')

def f_route_path(root, route):
	l = list(_f_route_path(root, route))
	l.reverse()
	return l

def f_route_identifier(route, *, warning=False):
	if warning:
		t = 'warning'
	else:
		try:
			t = route.fs_type()
		except OSError:
			t = 'warning'

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

	root = route@'/'
	return f_route_path(root, route.container) + f_route_identifier(route, warning=warning)

def f_route_absolute_colors(route, *, warning=False):
	for typ, value in f_route_absolute(route, warning=warning):
		yield (value, route_colors[typ])

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
