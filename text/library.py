"""
# Transform fault.text into XML.

# The &XML.transform class method provides the high-level interface
# for transforming fault.text into XML.

#!/pl/python
	text_iter = libtext.XML.transform('txt:', text, encoding='utf-8')
	sys.stdout.buffer.write(b''.join(text_iter))
"""
import itertools

from ..xml import library as libxml
from ..routes import library as libroutes
from ..computation import libstring

from . import core

# Much of this is write-once code.
# A rewrite using a parser-generator would be appropriate.

class XML(object):
	"""
	# Serialize parsed events into XML.

	# The eclectic parser produces event sequences and the serializer
	# provides the hierarchical structure necessary for XML.
	"""

	@classmethod
	def transform(Class, prefix:str, source:str, encoding:str='utf-8', identify=lambda x: x):
		"""
		# Construct an iterator producing XML from the given
		# eclectic documentation &source.

		# [ Parameters ]
		# /prefix
			# The element name prefix for the rendered XML.
		# /source
			# The eclectic text to transform into XML.
		# /encoding
			# The encoding that should be used for the XML.
		"""
		global core
		p = core.Parser()
		xmlctx = libxml.Serialization(xml_prefix=prefix, xml_encoding=encoding)
		s = Class(xmlctx, identify=identify)
		return s.serialize(p.parse(source))

	def __init__(self,
			serialization:libxml.Serialization,
			identify:object=lambda x: x,
		):
		"""
		# [ Parameters ]
		# /serialization
			# The serialization instance used to construct the XML.
		# /identify
			# The function used to prepare an identifier. Normally, a function
			# that prepends on some contextual identifier in order to guarantee
			# uniqueness. For example, `lambda x: 'ContextName' + x`.
		"""
		self.serialization = serialization
		self.identify = identify

	def serialize(self, tree):
		assert tree[0] == 'document'
		for section in tree[1]:
			yield from self.create_section(tree, section)

	def process_paragraph_text(self, tree, text, cast=None):
		yield from self.serialization.escape(text)

	def process_paragraph_emphasis(self, tree, data, weight=1):
		yield from self.serialization.prefixed('emphasis',
			self.serialization.escape(data),
			('weight', str(weight))
		)

	def process_paragraph_literal(self, tree, data, cast=None):
		yield from self.serialization.prefixed('literal',
			self.serialization.escape(data),
			('cast', cast),
		)

	def process_paragraph_reference(self, tree,
			source, type, title, action, cast=None,
		):
		"""
		# [ Parameters ]
		# /source
			# The reference source; the actual string found to be
			# identified as a reference.
		# /type
			# The type of reference, one of: `'hyperlink'`, `'section'`, `None`.
		# /action
			# The effect desired by the reference: `'include'` or &None.
			# &None being a normal reference, and `'include'` being induced
			# with a `'*'` prefixed to the reference
		"""

		yield from self.serialization.prefixed('reference',
			self.serialization.escape(source),
			('source', source), # canonical reference description
			('type', type),
			('action', action),
			('cast', cast), # canonical cast string
			('xlink:href', source[1:-1] if type == 'hyperlink' else None),
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
		chain = itertools.chain.from_iterable
		items = [
			(x[0], x[1], x[2] if x[2:] else None)
			for x in node[1]
			if x[0] in {'sequence-item', 'set-item'}
		]
		tail = node[1][len(items):]
		assert len(tail) == 0

		yield from chain((
			self.serialization.prefixed(name, chain([
					self.serialization.prefixed('item', chain((
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
		global itertools
		element = self.serialization.prefixed
		chain = itertools.chain.from_iterable

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
		if sequence and not self.empty_paragraph(sequence):
			yield from itertools.chain.from_iterable([
				self.paragraph_index[part[0]](self, tree, *part[1:])
				for part in sequence
			])
		else:
			# empty paragraph
			pass

	def process_paragraph(self, tree, paragraph, chain=itertools.chain.from_iterable):
		if paragraph[1] and not self.empty_paragraph(paragraph[1]):
			yield from self.serialization.prefixed('paragraph',
				chain([
					self.paragraph_index[part[0]](self, tree, *part[1:])
					for part in paragraph[1]
				]),
				('indentation', paragraph[2] if paragraph[2:] else None)
			)
		else:
			# empty paragraph
			pass

	def process_literals(self, tree, sequence):
		l = iter(sequence)
		element = self.serialization.prefixed
		escape = self.serialization.escape

		yield from element('literals',
			itertools.chain.from_iterable([
				element('line', escape(x))
				for x in sequence[1]
			]),
			('type', sequence[-1])
		)

	def process_admonition(self, tree, content):
		assert content[0] == 'admonition'
		global itertools
		element = self.serialization.prefixed

		# both the key and the value are treated as paragraph data.
		severity, title = content[2]
		yield from element('admonition',
			self.process_section(tree, ('admonition-content', content[1])),
			('severity', severity),
		)

	def process_section(self, tree, section):
		assert section[0] in ('section', 'variable-content', 'admonition-content', 'set-item')
		for part in section[1]:
			yield from self.section_index[part[0]](self, tree, part)

	def create_section(self, tree, section):
		title = section[-1]
		if title:
			ident = '.'.join(libstring.normal(x.replace(':', ''), separator='-') for x in title)
		else:
			ident = None

		yield from self.serialization.prefixed('section',
			self.process_section(tree, section),
			('identifier', title[-1] if title else None),
			('xml:id', self.identify(ident) if ident is not None else None),
		)

	def process_exception(self, tree, exception):
		"""
		# Emit an exception element in order to report warnings or failures
		# regarding syntax that was not entirely comprehensible.
		"""
		node_type, empty_content, msg, event, lineno, ilevel, params = exception
		yield from self.serialization.prefixed('exception',
			(),
			('event', event),
			('message', msg),
			('line', lineno),
			('indentation-level', ilevel),
		)

	def process_break(self, tree, node):
		"""
		# Break nodes are convenience structures created to
		# cease continuation of building a structure.
		"""
		return ()

	section_index = {
		'paragraph': process_paragraph,
		'set': process_set,
		'sequence': process_sequence,
		'dictionary': process_dictionary,
		'block': process_literals,
		'admonition': process_admonition,
		'break': process_break,
		'section': create_section,
		'exception': process_exception,
	}
