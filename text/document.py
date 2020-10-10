"""
# Document finalization and query tools for raw text node trees.
"""
import itertools
import typing
from ..context import string

from . import types

def export(paragraph, literal=None, reference=None) -> types.Paragraph:
	"""
	# Convert the given paragraph node into terms defined by &types.
	"""
	l = []
	former_type = None

	for x in paragraph:
		if isinstance(x, str):
			if not x:
				former_type = 'text/normal'
				continue

			if x == ' ' and former_type == 'text/normal':
				typ = 'text/line-break'
			else:
				typ = 'text/normal'
			former_type = typ

			l.append(types.Fragment((typ, x)))
		elif x[0] == 'emphasis':
			weight = str(x[-1].get('weight','1'))
			l.append(types.Fragment(('text/emphasis/'+weight, x[1][0])))
		elif x[0] == 'reference':
			rtype = x[-1]['type']
			cast = x[-1].get('cast') or reference

			if rtype == 'hyperlink':
				content = x[-1]['url']
				suffix = '/hyperlink'
			elif rtype == 'section':
				content = x[1][0]
				suffix = '/section'
			elif rtype == 'normal':
				content = x[-1]['source']
				suffix = '/ambiguous'

			if cast:
				cast = '/' + cast
			else:
				cast = ''

			l.append(types.Fragment(('reference'+suffix+cast, content)))
		elif x[0] == 'literal':
			cast = x[-1].get('cast') or literal
			if cast:
				cast = '/' + cast
			else:
				cast = ''
			l.append(types.Fragment(('literal/grave-accent'+cast, x[1][0])))

	return types.Paragraph(l)

def sections(root) -> typing.Iterator[typing.Tuple[str, object]]:
	"""
	# Iterator producing (section-identifier, section) pairs.
	"""
	for x in root:
		if x[0] == 'section':
			yield (x[-1]['identifier'], x)

def section(root, identifier) -> object:
	"""
	# Select the section with the given identifier.
	# Uses a full scan; index the results of &sections using a &dict
	# for repeat reads.
	"""

	for si, section_content in sections(root):
		if si == identifier:
			return section_content

	return None

def concatenate(syntax) -> typing.Iterator[str]:
	"""
	# Concatenate the lines of the given syntax node.
	"""
	for x in syntax[1]:
		if x[0] == 'line':
			yield x[1][0]
			yield '\n'

def context(node):
	"""
	# Structure a common context admonition.
	"""
	items = node[0][0][1]
	return dict(dictionary_pairs(items))

def paragraph_as_string(node):
	t, c, a = node

	return ''.join(
		''.join(x[1] or x[-1]['source']) if not isinstance(x, str) else x
		for x in c
		if x is not None
	)

def paragraph_only(node):
	"""
	# Select the only paragraph in the given node.
	"""
	t, c, a = node
	assert t == 'paragraph'

	if len(c) == 1:
		return c[0]
	else:
		return None

def paragraph_first(node):
	"""
	# Select the first paragraph in the given node.
	"""
	for x in node[1]:
		if not isinstance(x, str) or x:
			return x

def paragraph_last(node):
	"""
	# Select the last paragraph in the given node.
	"""
	for x in reversed(node[1]):
		if not isinstance(x, str) or x:
			return x

def paragraph_lines(node):
	t, c, a = node
	assert t == 'paragraph'

	init_line = True
	current = []
	for x in c:
		if isinstance(x, str) and not x:
			if init_line:
				init_line = False
				append(current)
				current = []

def interpret_reference(node):
	t, c, a = node
	assert t == 'reference'
	ref = a.get('url') or (c and c[0]) or a.get('source')

	return Reference(ref, a.get('type'), a.get('cast'))

def interpret_paragraph_single(node):
	if isinstance(node, str):
		return node

	t, c, *a = node
	if t == 'literal':
		return c[0]
	elif t == 'reference':
		return interpret_reference(node)

def dictionary_pairs(items:list):
	"""
	# Iterate over the key-value pairs in the dictionary items.
	"""
	# Identify the key-value pairs of dictionaries.
	for i in items:
		key, value = i[1]
		k = key[1][0]
		v = value[1][0]
		yield k, v

class Tree(object):
	"""
	# Serializer for (text) object trees.
	"""

	def __init__(self):
		"""
		# Initialize the tree builder.
		"""
		pass

	def empty(self, name, *args, **kw):
		"""
		# Empty with potential attributes.
		"""
		return self.element(name, None, *args, **kw)

	def element(self, element_name, content, *attributes, **kwattributes):
		"""
		# Serialize an element with the exact &element_name with the contents of
		# &subnode_iterator as the inner nodes. &subnode_iterator must produce
		# &bytes encoded objects.
		"""

		return [(element_name, list(content) if content is not None else None, dict(attributes))]

	prefixed = element

	def escape(self, string):
		return [string]

	def hyperlink(self, href):
		return ('url', href)

class Transform(object):
	"""
	# Transform parse events into a form designated by the given AST constructor.
	"""
	chain = staticmethod(itertools.chain.from_iterable)

	def __init__(self, serialization, identify=(lambda x: x)):
		"""
		# Initialize a &Transform instance designating the AST constructor.

		# [ Parameters ]

		# /serialization/
			# The serialization instance used to construct the tree.
		# /identify/
			# The function used to prepare an identifier. Normally, a function
			# that prepends on some contextual identifier in order to guarantee
			# uniqueness. For example, `lambda x: 'ContextName' + x`.
		"""
		self.serialization = serialization
		self.identify = identify
		self.emit = self.serialization.prefixed
		self.text = self.serialization.escape

	def process(self, tree):
		assert tree[0] == 'chapter'
		return ('chapter', list(self.process_section(tree, tree)), tree[2])

	def process_paragraph_text(self, tree, text, cast=None):
		yield from self.text(text)

	def process_paragraph_emphasis(self, tree, data, weight=1):
		yield from self.emit('emphasis',
			self.text(data),
			('weight', str(weight))
		)

	def process_paragraph_literal(self, tree, data, cast=None):
		yield from self.emit('literal',
			self.text(data),
			('cast', cast),
		)

	def process_paragraph_reference(self, tree,
			source, type, title, action, cast=None,
		):
		"""
		# [ Parameters ]
		# /source/
			# The reference source; the actual string found to be
			# identified as a reference.
		# /type/
			# The type of reference, one of: `'hyperlink'`, `'section'`, `None`.
		# /action/
			# The effect desired by the reference: `'include'` or &None.
			# &None being a normal reference, and `'include'` being induced
			# with a `'*'` prefixed to the reference
		"""
		escape = self.text
		element = self.emit

		href = None
		if type == 'section':
			sstr = escape(source[1:-1].strip())
		elif type == 'hyperlink':
			href = source[1:-1]
			if href[0:1] == '[':
				eot = href.find(']')
				if eot == -1:
					# no end for title. essentially a syntax error,
					# so a warning element should be presented.
					pass
				else:
					sstr = escape(href[1:eot])
					href = href[eot+1:]
			else:
				# no title indicator.
				sstr = None
		else:
			# Normal reference.
			sstr = escape(source)

		yield from element('reference',
			sstr,
			('source', source), # canonical reference description
			('type', type),
			('action', action),
			('cast', cast), # canonical cast string
			self.serialization.hyperlink(href),
		)

	def process_end_of_line(self, tree, text, cast=None):
		return ()

	def process_init(self, tree, data, *params):
		return ()

	paragraph_index = {
		'init': process_init,
		'text': process_paragraph_text,
		'eol': process_end_of_line,
		'emphasis': process_paragraph_emphasis,
		'literal': process_paragraph_literal,
		'reference': process_paragraph_reference,
	}

	def process_items(self, tree, node, name):
		chain = self.chain
		items = [
			(x[0], x[1], x[2] if x[2:] else None)
			for x in node[1]
			if x[0] in {'sequence-item', 'set-item'}
		]
		tail = node[1][len(items):]
		assert len(tail) == 0 # Failed to switch to new set of items.

		yield from chain((
			self.emit(name, chain([
					self.emit('item', chain((
							self.section_index[y[0]](self, tree, y) for y in x[1]
						)),
					)
					for x in items
				])
			),
		))

	def process_set(self, tree, node):
		return self.process_items(tree, node, 'set')

	def process_sequence(self, tree, node):
		return self.process_items(tree, node, 'sequence')

	def process_dictionary(self, tree, vl_node):
		assert vl_node[0] == 'dictionary'
		element = self.emit
		chain = self.chain

		# both the key is treated as paragraph data, but value is section data.
		content = vl_node[1]
		key_nodes = content[0::2]

		keys = [element('key',
			chain([
				self.paragraph_index[part[0]](self, tree, *part[1:])
				for part in parts
			])) for parts in (x[1] for x in key_nodes)
		]

		# The period characters need to be transformed in order
		key_ids = [
			''.join([part[1] for part in parts]).replace('.', '∙')
			for parts in (x[1] for x in key_nodes)
		]

		values = [
			element('value', chain([self.process_section(tree, part)]))
			for part in content[1::2]
		]

		yield from element('dictionary',
			chain([
				element('item', chain(x), ('identifier', key_id))
				for key_id, x in zip(key_ids, zip(keys, values))
			])
		)

	@staticmethod
	def empty_paragraph(sequence):
		"""
		# Whether the paragraph should be considered to be empty.
		"""
		for i in sequence:
			if i == ('init', ''):
				continue
			if i == ('eol', ''):
				continue
			if i[0] == 'text' and i[1].isspace():
				continue

			# Content; return False.
			break
		else:
			# Consists of spaces or signal tokens.
			return True

		return False

	def paragraph_content(self, tree, sequence):
		chain = self.chain
		if sequence and not self.empty_paragraph(sequence):
			yield from chain([
				self.paragraph_index[part[0]](self, tree, *part[1:])
				for part in sequence
			])
		else:
			# empty paragraph
			pass

	def process_paragraph(self, tree, paragraph):
		chain = self.chain
		if paragraph[1] and not self.empty_paragraph(paragraph[1]):
			if paragraph[1][-1][1].isspace():
				# Filter trailing spaces inserted by presumption of a following line.
				del paragraph[1][-1]

			para = paragraph[1]
			yield from self.emit('paragraph',
				chain([
					self.paragraph_index[part[0]](self, tree, *part[1:])
					for part in para
				]),
				('indentation', paragraph[2] if paragraph[2:] else None)
			)
		else:
			# empty paragraph
			pass

	def process_syntax(self, tree, sequence):
		chain = self.chain
		l = iter(sequence)
		element = self.emit
		escape = self.text
		designation = sequence[-1].split(' ', 1)

		yield from element('syntax',
			chain([
				element('line', escape(x))
				for x in sequence[1]
			]),
			('type', designation[0]),
			('qualifier', designation[1] if designation[1:2] else None),
		)

	def process_admonition(self, tree, content):
		assert content[0] == 'admonition'
		element = self.emit

		# both the key and the value are treated as paragraph data.
		atype, title = content[2]
		yield from element('admonition',
			self.process_section(tree, ('admonition-content', content[1])),
			('type', atype),
			('title', title),
		)

	def process_section(self, tree, section):
		assert section[0] in ('chapter', 'section', 'variable-content', 'admonition-content', 'set-item')
		for part in section[1]:
			yield from self.section_index[part[0]](self, tree, part)

	def create_section(self, tree, section):
		title, sl, sl_m, spath = (section[-1] or (None, None, None, None))
		if title:
			abs_ident = title
			ident = title[-1]
		else:
			abs_ident = None
			ident = None

		yield from self.emit('section',
			self.process_section(tree, section),
			('identifier', ident),
			('absolute', abs_ident),
			('selector-path', spath),
			('selector-level', sl),
			('selector-multiple', sl_m),
		)

	def process_exception(self, tree, exception):
		"""
		# Emit an exception element in order to report warnings or failures
		# regarding syntax that was not entirely comprehensible.
		"""
		node_type, empty_content, msg, event, lineno, ilevel, params = exception
		yield from self.emit('exception',
			(),
			('event', event),
			('message', msg),
			('line', lineno),
			('indentation-level', ilevel),
		)

	section_index = {
		'paragraph': process_paragraph,
		'set': process_set,
		'sequence': process_sequence,
		'dictionary': process_dictionary,
		'syntax': process_syntax,
		'admonition': process_admonition,
		'section': create_section,
		'exception': process_exception,
	}
