"""
# fault Text nodes implementations and parsing functionality.
"""
import itertools

from ..computation import string

from . import core

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
		assert tree[0] == 'document'
		for section in tree[1]:
			yield from self.create_section(tree, section)

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

		yield from element('syntax',
			chain([
				element('line', escape(x))
				for x in sequence[1]
			]),
			('type', sequence[-1])
		)

	def process_admonition(self, tree, content):
		assert content[0] == 'admonition'
		element = self.emit

		# both the key and the value are treated as paragraph data.
		atype, title = content[2]
		yield from element('admonition',
			self.process_section(tree, ('admonition-content', content[1])),
			('type', atype),
		)

	def process_section(self, tree, section):
		assert section[0] in ('section', 'variable-content', 'admonition-content', 'set-item')
		for part in section[1]:
			yield from self.section_index[part[0]](self, tree, part)

	def create_section(self, tree, section):
		title = section[-1]
		if title:
			ident = '.'.join(string.normal(x.replace(':', ''), separator='-') for x in title)
		else:
			ident = None

		yield from self.emit('section',
			self.process_section(tree, section),
			('identifier', title[-1] if title else None),
			('absolute', self.identify(ident) if ident is not None else None),
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

	def process_directive(self, tree, data):
		event, signal, *parameter = data
		yield from self.emit(
			event,
			(),
			('signal', signal),
			('parameter', parameter[0] if parameter else None),
		)

	def process_break(self, tree, node):
		"""
		# Break nodes are convenience structures created to
		# cease continuation of building a structure.
		"""
		return ()

	section_index = {
		'directive': process_directive,
		'paragraph': process_paragraph,
		'set': process_set,
		'sequence': process_sequence,
		'dictionary': process_dictionary,
		'block': process_syntax,
		'syntax': process_syntax,
		'admonition': process_admonition,
		'break': process_break,
		'section': create_section,
		'exception': process_exception,
	}
