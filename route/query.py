"""
# Tools for navigating element trees.

# Provides the &Cursor class for navigating and retrieving nodes identified
# using a limited path language.
"""
from collections.abc import Sequence, Mapping
import itertools
import functools

from ..context import comethod
from ..syntax import keywords

class InvalidPath(Exception):
	"""
	# Path string given to &Context.prepare was not valid.
	"""

def iselement(subject, *, len=len, isinstance=isinstance):
	"""
	# Determines whether the given object has the properties of an element.
	"""
	try:
		# Explicit signal.
		return subject[2]['[element]']
	except KeyError:
		# Maybe.
		pass
	except Exception:
		# Never an element.
		return False

	if len(subject) != 3:
		return False
	if not isinstance(subject[2], Mapping):
		return False
	if not isinstance(subject[1], Sequence):
		return False
	if not isinstance(subject[0], str):
		return False

	return True

class Context(comethod.object):
	"""
	# Query expression context for parsing and interpreting paths.
	"""

	def prepare(self, path:str):
		"""
		# Parse the path string into a selection plan.
		"""
		tokens, = map(list, self._parser([path]))
		return list(self.structure(tokens))

	# Construct a tokenizer for parsing paths.
	_paths_profile = keywords.Profile.from_keywords_v1(
		routers = ["/"],
		operations = [
			"*", # Match any immediate descendant.
			"#", # Slice nodes. 1-based, inclusive.
			"?", # Apply context designated filter.

			"\\\\", # Escape backslash in predicate string.
			"\\]", # Escape predicate close.
			"|",
		],
		terminators = [],
		enclosures = [],
		literals = [
			["[", "]"], # Predicates are text strings.
		],
	)
	_parser = keywords.Parser.from_profile(_paths_profile).process_document

	def __init__(self, selectors, aliases, filters=None, identify=None):
		self.selectors = selectors
		if selectors:
			selectors.add('*')
		self.aliases = aliases
		self.filters = filters or dict()
		self.identify = identify or self._identify_node

	@staticmethod
	def _identify_node(predicate, node):
		# Default identify configuration.
		if node[2].get('identifier', '') == predicate:
			yield node

	@staticmethod
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

	@staticmethod
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

	def structure(self, tokens, start=0):
		"""
		# Process tokens into selector sequences.
		# Usually used indirectly by &prepare.
		"""
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
				# Consumption of the entire literal is possible
				# as the terminating token is required.
				string = self._read_string(Tokens)
				nodes.append((cursor+1, 'predicate', string))
				cursor += len(string) + 1
			elif typ == 'identifier' and node is None:
				if not closed:
					raise InvalidPath("multiple element selectors present in path segment")

				closed = False
				if self.selectors and txt not in self.selectors:
					try:
						nid = self.aliases[txt] # Invalid element type.
					except KeyError:
						raise InvalidPath("unrecognized element type")
				else:
					nid = txt

				nodes.append((cursor, 'select', nid))
			elif t == ('operation', 'event', '#'):
				if node is not None:
					nodes.append(tuple(node))
				node = [cursor, 'index']
			elif t == ('operation', 'event', '*'):
				if not closed:
					raise InvalidPath("multiple element selectors present in path segment")

				nodes.append((cursor, 'all', 'required'))
				closed = False
			elif t == ('operation', 'event', '?'):
				if node is not None:
					nodes.append(tuple(node))
				node = [cursor, 'filter', '?']
			elif node is not None:
				if typ == 'identifier':
					# NOTE: This should actually be contained within
					# the index and filter cases, but the loop cannot
					# peek or replay tokens as-is.
					if node[1] == 'index':
						try:
							node.append(self._parse_slice(txt))
							nodes.append(node)
							node = None
						except Exception:
							raise InvalidPath("invalid slice at %d, %r" %(cursor, txt))
					elif node[1] == 'filter' and txt not in self.filters:
						raise InvalidPath("unknown filter at %d, %r" %(cursor, txt))
					else:
						node.append(txt)
				else:
					node.append(txt)
			elif typ == 'switch':
				pass
			else:
				raise InvalidPath("unexpected token at %d, %r" %(cursor, t))

			cursor += len(txt)

		if node is not None:
			nodes.append(tuple(node))
		if open_union is not None:
			open_union.append(nodes)
			nodes = [prefix, (-1, 'union', open_union)]

		yield nodes
		yield [(cursor, 'end', '')]

	@comethod('select')
	def _select(self, nodes, ident):
		for x in nodes:
			if x[0] == ident:
				yield x

	@comethod('index')
	def _index(self, nodes, eslice):
		return nodes[eslice]

	@comethod('predicate')
	def _predicate(self, nodes, title):
		idg = self.identify
		for x in nodes:
			yield from idg(title, x)

	@comethod('all')
	def _all(self, nodes, type):
		assert type == 'required'
		return nodes

	@comethod('filter')
	def _filter(self, nodes, *spec):
		f_id = ''.join(spec[1:])
		try:
			f = self.filters[f_id]
		except Exception as exc:
			raise LookupError("requested filter is not available in cursor") from exc

		for x in nodes:
			if f(x):
				yield x

	@comethod('union')
	def _union(self, origin_nodes, exprnodes):
		on = list(origin_nodes)
		for series in exprnodes:
			nodes = on
			for x in series:
				nodes = list(self.switch(x, nodes))

			yield from nodes

	def switch(self, operation, nodes, *, getattr=getattr):
		return self.comethod(operation[1])(nodes, *operation[2:])

	def interpret(self, plan, root, context, *, chain=itertools.chain.from_iterable, list=list):
		# Interpret &plan against &root and &context.

		# Identify initial position.
		postinit = plan[0][1:] + plan[1][:1]
		if postinit[0] == (postinit[0][0], 'partition', '/'):
			nodes = root
			start = 1
		else:
			nodes = context
			start = 0

		# Interprete each series of path nodes.
		for series in plan[start:]:
			if len(series) == 1:
				# Empty series (nothing more than a '/').
				continue

			# Apply the operations to the content of elements in &nodes.
			nodes = chain(x[1] for x in nodes)
			for op in series[1:]:
				nodes = list(self.switch(op, nodes))

		return nodes

class Cursor(object):
	"""
	# Navigation state class providing a query interface to an element tree.
	"""

	def __init__(self, context, root):
		self.context = context
		self.root = root
		self._context_node = self.root
		self._prepare = context.prepare
		self._interpret = context.interpret

	def seek(self, path):
		"""
		# Adjust the cursor position to the nodes identified by &path.
		"""
		self._context_node = self._interpret(self._prepare(path), self.root, self._context_node)
		return self

	def reset(self):
		"""
		# Select the root as the current working node.
		"""
		self._context_node = self.root
		return self

	def fork(self, path):
		"""
		# Create a new instance using the given &path to the select the nodes
		# used as the root content of the new &Cursor.
		"""
		nodes = self.select(path)
		return self.__class__(self.context, nodes)

	def select(self, path):
		"""
		# Retrieve nodes relative to the context node using &path.
		"""
		return self._interpret(self._prepare(path), self.root, self._context_node)
