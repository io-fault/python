"""
Eclectic XML transformation.
Parse eclectic text into a nested structure primarily intended for XML serialization.
Eclectic Text is a structured text language that attempts to borrow syntax from
popular languages in order to create memorable notations. By associating a given notation
with a familiar origin, the syntax is thought to be more recollectable than most.

Eclectic is structured as a sequence of commands with style ranges; each line represents
a command. Whether a new paragraph, a null command (empty line), or new section. Style
ranges do not cross commands (lines) and must be explicitly continued by finishing the
style and starting it again.
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
	Serialize parsed events into XML.

	The eclectic parser produces event sequences and the serializer
	provides the hierarchical structure necessary for XML.
	"""

	def __init__(self,
			serialization:libxml.Serialization,
			identify:object=lambda x: x,
		):
		"""
		[ Parameters ]

		/&serialization
			The serialization instance used to construct the XML.
		/&identify
			The function used to prepare an identifier. Normally, a function
			that prepends some contextual identifier in order to guarantee
			uniqueness.
		"""
		self.serialization = serialization
		self.identify = identify

	def process_paragraph_text(self, tree, text, cast=None):
		yield from self.serialization.escape(text)

	def process_end_of_line(self, tree, text, cast=None):
		return ()

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
		[ Parameters ]

		/&source
			The reference source; the actual string found to be
			identified as a reference.
		/&type
			The type of reference, one of: `'hyperlink'`, `'section'`, `None`.
		/&action
			The effect desired by the reference: `'include'` or &None.
			&None being a normal reference, and `'include'` being induced
			with a `'*'` prefixed to the reference
		"""

		yield from self.serialization.prefixed('reference',
			self.serialization.escape(source),
			('source', source), # canonical reference description
			('type', type),
			('action', action),
			('cast', cast), # canonical cast string
			('xlink:href', source if type == 'hyperlink' else None),
		)

	paragraph_index = {
		'text': process_paragraph_text,
		'eol': process_end_of_line,
		'emphasis': process_paragraph_emphasis,
		'literal': process_paragraph_literal,
		'reference': process_paragraph_reference,
	}

	def process_set(self, tree, node):
		chain = itertools.chain.from_iterable
		items = node[1]

		yield from self.serialization.prefixed('set', chain([
				self.serialization.prefixed('item', self.paragraph_content(tree, x[1]))
				for x in items
			])
		)

	def process_sequence(self, tree, node):
		chain = itertools.chain.from_iterable
		items = node[1]

		yield from self.serialization.prefixed('sequence', chain([
				self.serialization.prefixed('item', self.paragraph_content(tree, x[1]))
				for x in items
			])
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

	def process_dictionary(self, tree, vl_node):
		assert vl_node[0] == 'dictionary'
		global itertools
		element = self.serialization.prefixed
		chain = itertools.chain.from_iterable

		# both the key and the value are treated as paragraph data.
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

	def paragraph_content(self, tree, sequence):
		global itertools

		if sequence:
			yield from itertools.chain.from_iterable([
				self.paragraph_index[part[0]](self, tree, *part[1:])
				for part in sequence
			])
		else:
			# empty paragraph
			pass

	def process_paragraph(self, tree, paragraph, chain=itertools.chain.from_iterable):
		if paragraph[1]:
			yield from self.serialization.prefixed('paragraph',
				chain([
					self.paragraph_index[part[0]](self, tree, *part[1:])
					for part in paragraph[1]
				])
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

	def process_section(self, tree, section):
		assert section[0] in ('section', 'variable-content', 'admonition-content')
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

	def process_break(self, tree, node):
		"""
		Break nodes are convenience structures created to
		cease continuation of building a structure.
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
	}

	def serialize(self, tree):
		assert tree[0] == 'document'
		for section in tree[1]:
			yield from self.create_section(tree, section)

	@classmethod
	def transform(Class, prefix:str, source:str, encoding:str='utf-8', identify=lambda x: x):
		"""
		Construct an iterator producing XML from the given
		eclectic documentation &source.
		"""

		p = core.Parser()
		s = Class(libxml.Serialization(prefix, encoding), identify=identify)
		return s.serialize(p.parse(source))
