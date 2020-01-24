"""
# Tools for navigating the nodes of parsed text documents.

# Provides the &Cursor class for navigating and retrieving nodes identified
# using a limited path language.

# [ Engineering ]
# Currently, this implements a near the bare minimum functionality and needs improvement.
# Much of the parsing functions should be housed in a Context class along with filtering
# configuration.
# Parse tree structuring is performed using a very inefficient function and
# predicates are not pushed down yielding much unnecessary copying of nodes.
"""
import itertools
import functools

from . import document
from . import format

class Error(Exception):
	"""
	# Base class for text node and path specific errors.
	"""

class PathSyntaxError(Error):
	"""
	# Path string was not valid.
	"""

class ContextMismatch(Error):
	"""
	# &Cursor could not perform an operation due to a misconfiguration
	# of the cursor or due to the use of an errant path.
	"""

from ..syntax import keywords as kos
text_paths_profile = kos.Profile.from_keywords_v1(
	routers = ["/"],
	operations = [
		".", # Self
		"*", # Match any immediate descendant.
		"#", # Slice nodes.
		"?", # Apply context designated filter.

		"\\\\", # Escape backslash in predicate string.
		"\\]", # Escape predicate close.
		"|",
	],
	terminators = [],
	enclosures = [],
	literals = [
		["[", "]"], # Predicates are mere text strings.
	],
)

text_paths_parser = kos.Parser.from_profile(text_paths_profile)
del kos

selectors = set([
	'paragraph',
	'syntax',
	'line',

	'chapter',
	'section',
	'admonition',
	'dictionary',
	'sequence',
	'set',

	'item',
	'key',
	'value',
	'*',
	'.',
])

aliases = {
	'dict': 'dictionary',
	'sect': 'section',
	'para': 'paragraph',
	'p': 'paragraph',
	'i': 'item',
	'seq': 'sequence',
}

def _read_string(itokens, terminator=('literal', 'stop', ']')):
	string = ""
	for i in itokens:
		if i == terminator:
			break
		else:
			if i[2] == "\\\\":
				string += "\\"
			elif i[2] == "\\]":
				string += "]"
			else:
				string += i[2]

	return string

def _structure(tokens, start=0):
	cursor = start
	nodes = [(cursor, 'init', '')]
	closed = True
	open_union = None
	node = None

	Tokens = iter(tokens)
	for t in Tokens:
		typ, qual, txt = t

		if (typ, txt) == ('router', '/'):
			if node is not None:
				nodes.append(tuple(node))
				node = None

			if open_union is not None:
				open_union.append(nodes)
				nodes = [prefix, (-1, 'union', open_union)]
				open_union = None
				del prefix

			yield nodes
			nodes = []
			nodes.append((cursor, 'partition', txt))
			closed = True
		elif t == ('operation', 'event', '|'):
			if node is not None:
				nodes.append(tuple(node))
				node = None

			if open_union is None:
				open_union = [nodes[1:]]
				prefix = nodes[0]
			else:
				open_union.append(nodes)
			nodes = []
			closed = True
		elif t == ('literal', 'start', '['):
			string = _read_string(Tokens)
			nodes.append((cursor+1, 'predicate', string))
			cursor += len(string) + 1
		elif typ == 'identifier' and node is None:
			if not closed:
				raise PathSyntaxError("multiple node class selectors present in path segment")

			closed = False
			if txt not in selectors and txt[:1] != '@':
				try:
					nid = aliases[txt] # Invalid node class identifier.
				except:
					raise PathSyntaxError("unrecognized node class identifier")
			else:
				nid = txt

			nodes.append((cursor, 'select', nid))
		elif t == ('operation', 'event', '#'):
			node = [cursor, 'index']
		elif t == ('operation', 'event', '*'):
			if not closed:
				raise PathSyntaxError("multiple node class selectors present in path segment")

			nodes.append((cursor, 'all', 'required'))
			closed = False
		elif t == ('operation', 'event', '?'):
			node = [cursor, 'filter', '?']
		elif t == ('operation', 'event', '.') and closed == True:
			closed = False
			nodes.append((cursor, 'self', '.'))
		elif node is not None:
			node.append(txt)
		elif typ == 'switch':
			pass
		else:
			raise PathSyntaxError("unexpected token at %d, %r" %(cursor, t))

		cursor += len(txt)

	if node is not None:
		nodes.append(tuple(node))
	if open_union is not None:
		open_union.append(nodes)
		nodes = [prefix, (-1, 'union', open_union)]

	yield nodes
	yield [(cursor, 'end', '')]

def _parse_slice(string):
	step = 1
	ss = string.split('-', 1)
	if len(ss) == 1:
		stop = int(ss[0])
		start = stop - 1
	else:
		start, stop = map(int, ss)
		start -= 1

	return slice(start, stop, step)

class Cursor(object):
	"""
	# Navigation state class providing a query interface to a text node tree.
	"""

	@staticmethod
	def _parse_text(source,
			Parser=format.Parser,
			Transform=document.Transform,
			dt=document.Tree()
		):

		dx = Transform(dt)
		fp = Parser()
		g = dx.process(fp.parse(source))
		return list(g)

	@classmethod
	def from_chapter_content(Class, nodes, identifier=None):
		"""
		# Create an instance using the given &nodes.

		# The nodes are set as the content of a new chapter node.
		"""
		chapter = [('chapter', nodes, {'identifier':identifier})]
		return Class(chapter)

	@classmethod
	def from_chapter_text(Class, text:str, identifier=None):
		"""
		# Create an instance using a root node built from the given &text.
		"""
		content = Class._parse_text(text)
		return Class.from_chapter_content(content)

	def __init__(self, root):
		self.root = root
		self.filters = {}
		self._context_path = []
		self._context_node = self.root

	def move(self, path, list=list, chain=itertools.chain.from_iterable):
		"""
		# Adjust the cursor position to the nodes identified by &path.
		"""
		self._context_node = self.select(path)
		return self

	def fork(self, path):
		"""
		# Create a new instance using the given &path to the select the nodes
		# used as the root content of the new &Cursor.
		"""
		nodes = self.select(path)
		fragments = [('fragment', nodes, {'origin': path})]
		c = self.__class__(fragments)
		c.filters = self.filters

	def _select(self, nodes, ident):
		for x in nodes:
			if x[0] == ident:
				yield x

	@staticmethod
	def _is_identified(node, title):
		attr = node[-1]
		try:
			if node[0] in ('admonition', 'syntax'):
				if attr['type'] == title:
					return True
			else:
				if attr['identifier'] == (title or None):
					return True
		except:
			# Likely paragraph.
			pass

		return False

	def _index(self, nodes, number):
		return nodes[_parse_slice(number)]

	def _predicate(self, nodes, title):
		for x in nodes:
			if x[0] == 'dictionary':
				for y in x[1]:
					if y[-1]['identifier'] == title:
						yield y[1][-1]
			elif x[0] == 'sequence':
				yield from x[1][_parse_slice(title)]
			elif self._is_identified(x, title):
				yield x

	def _all(self, nodes, type):
		assert type == 'required'
		return nodes

	def _filter(self, nodes, *spec):
		f_id = ''.join(spec[1:])
		try:
			f = self.filters[f_id]
		except Exception as exc:
			raise ContextMismatch("requested filter is not available in cursor") from exc

		for x in nodes:
			if f(x):
				yield x

	def _self(self, nodes, ident):
		yield ('self', nodes, None)

	def _union(self, origin_nodes, exprnodes):
		product = []
		for series in exprnodes:
			nodes = origin_nodes
			for x in series:
				nodes = list(self._apply_method(nodes, x))

			product.extend(nodes)
		yield ('union', product, {'expressions': len(exprnodes)})

	_methods = {
		'self': _self,
		'select': _select,
		'predicate': _predicate,
		'index': _index,
		'all': _all,
		'filter': _filter,
		'union': _union,
	}

	def _apply_method(self, nodes, request):
		m = self._methods[request[1]]
		return m(self, nodes, *request[2:])

	@classmethod
	def prepare(Class, path, parser=text_paths_parser.process_document) -> None:
		"""
		# Prepare node path for execution.
		"""
		tokens, = map(list, parser([path]))
		return _structure(tokens)

	@classmethod
	@functools.lru_cache(16)
	def _cached_prepare(Class, path):
		ps = list(Class.prepare(path))

		if ps[1][0][0] == (ps[1][0], 'partition', '/'):
			# Leading / selecting from root.
			rootctx = True
		else:
			rootctx = False
			ps.insert(0, None) # Maintain invariant; provide false init entry to be skipped.

		return rootctx, ps

	def select(self, path, list=list, chain=itertools.chain.from_iterable):
		"""
		# Retrieve nodes relative to the context node using &path.
		"""
		final = {'paragraph', 'line'}
		rootctx, ps = self._cached_prepare(path)

		if rootctx:
			nodes = self.root
		else:
			nodes = self._context_node

		for series in ps[1:-1]:
			series = series[1:]
			if series:
				nodes = list(chain(x[1] for x in nodes if x[0] not in final))
			origin = nodes

			for x in series:
				nodes = list(self._apply_method(nodes, x))

		return nodes

	def _syntax_struct(node):
		attrs = node[-1]
		lines = [x[1][0] for x in node[1]]
		return (attrs['type'], attrs.get('qualifier'), lines)

	def _paragraph_struct(node, export=document.export):
		return export(node[1])

	_exports = {
		'paragraph': _paragraph_struct,
		'syntax': _syntax_struct,
	}

	def export(self, path):
		"""
		# Select and convert the returned nodes using the export
		# configuration of the cursor.
		"""
		ex = self._exports

		for node in self.select(path):
			try:
				xf = self._exports[node[0]]
			except KeyError:
				yield node
			else:
				yield xf(node)
