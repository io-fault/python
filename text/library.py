"""
Eclectic XML transformation and Context configuration.
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

class Namespace(object):
	"""
	Base class for Context Scopes for resolving references.
	"""

	def select(self, reference, cast=None):
		"""
		Select the target associated with the given reference.
		"""
		pass

class TextNamespace(Namespace):
	"""
	An eclectic text scope for section references and explicit address
	declarations.

	[ Attributes ]

	/prefix
		The prefix applied to the slugified section titles.
		Primarily used by doc-strings that seek to qualify
		the unique identifier.

	/structs
		The set of structured documents to index. The section titles
		are transformed 
	"""

	def construct(self, structs):
		# construct the index
		# built after the document has been parsed
		self.index = {}

		for ds in self.structs:
			for section in ds:
				if sections[0] != 'section':
					continue
				nt, content, title = section
				self.index[self.prepare(title)] = section

	def __init__(self, prefix, *eclectic_structs):
		self.prefix = prefix
		self.structs = eclectic_structs
		self.construct(self.structs)

	def select(self, reference, cast=None):
		if reference in self.index:
			return self.index[reference]
		else:
			return super().select(reference)

class PythonNamespace(Namespace):
	"""
	Resolve absolute attribute path to its (module, attribute path) pair.
	"""
	import builtins

	def select(self, reference, cast=None):
		r = libroutes.Import.from_fullname(reference).real()
		if r is None:
			# try builtins.
			fn = 'builtins'
			module = self.builtins
			attr_path = reference
		else:
			fn = r.fullname
			module = r.module()
			attr_path = reference[len(fn):].strip('.')
			if not attr_path:
				# module reference.
				return (fn, None, [(fn, module)])

		objects = []
		obj = module
		name = fn
		for x in attr_path.split('.'):
			objects.append((name, obj))
			name = x
			obj = getattr(obj, name)
		else:
			objects.append((name, obj))

		return (fn, attr_path, objects)

class PythonRelativeNamespace(PythonNamespace):
	"""
	Resolve Python references as the superclass with the exception
	of `'.'` prefixed references which are qualified with the configured
	prefix in order to identify its absolute path.

	This allows for documentation to reference objects relative to the bottom
	package.
	"""

	def __init__(self, prefix):
		self.prefix = prefix

	def select(self, reference, cast=None):
		if reference.startswith('.'):
			reference = self.prefix + reference

		return super().select(reference)

class PythonContextNamespace(Namespace):
	"""
	Resolve a Python reference based on context objects providing the index used.

	Python Context namespaces are used to resolve relative references
	"""

	def __init__(self, module, objects):
		self.module = module
		self.objects = objects

	def select(self, reference, cast=None):
		for name, obj in self.objects:
			pass
		return (module.__name__, ...)

class Context(object):
	"""
	The processing context used to resolve references and construct or validate data
	structures from casted literals.

	Contexts consists of a sequence of scopes that are used to look for the reference's
	target. When the target is found, the source, link, and type are produced for
	a reference element to communicate how the final link is to be built.
	"""

	def __init__(self, *namespaces):
		self.namespaces = namespaces

	def select(self, reference, cast:str=None):
		"""
		Scan the configured namespaces for the reference's addressing.
		"""

		for x in self.namespaces:
			data = x.select(reference, cast)
			if data is not None:
				return data
		return None

class XML(object):
	"""
	Serialize parsed events into XML.

	The eclectic parser produces event sequences and the serializer
	provides the hierarchical structure necessary for XML.
	"""

	def __init__(self,
			context:Context,
			serialization:libxml.Serialization,
			identify:object=lambda x: x,
		):
		"""
		[ Parameters ]

		/&context
			The reference resolution Context to use to extract
			abstract reference information.
		/&serialization
			The serialization instance used to construct the XML.
		/&identify
			The function used to prepare an identifier. Normally, a function
			that prepends some contextual identifier in order to guarantee
			uniqueness.
		"""
		self.serialization = serialization
		self.context = context
		self.identify = identify

	def process_paragraph_text(self, addresses, tree, text, cast=None):
		yield from self.serialization.escape(text)

	def process_paragraph_emphasis(self, addresses, tree, data, weight=1):
		yield from self.serialization.prefixed('emphasis', 
			self.serialization.escape(data),
			('weight', str(weight))
		)

	def process_paragraph_literal(self, addresses, tree, data, cast=None):
		yield from self.serialization.prefixed('literal',
			self.serialization.escape(data),
			('cast', cast),
		)

	def process_paragraph_reference(self, addresses, tree, data, cast=None):
		#display, qualities, links = self.context.select(data, cast=cast)

		yield from self.serialization.prefixed('reference',
			self.serialization.escape(data),
			('source', data), # canonical reference description
			('cast', cast), # canonical cast string
			('xlink:href', None),
		)

	paragraph_index = {
		'text': process_paragraph_text,
		'emphasis': process_paragraph_emphasis,
		'literal': process_paragraph_literal,
		'reference': process_paragraph_reference,
	}

	def process_set(self, addresses, tree, node):
		chain = itertools.chain.from_iterable
		items = node[1]

		yield from self.serialization.prefixed('set', chain([
				self.serialization.prefixed('item', self.paragraph_content(addresses, tree, x[1]))
				for x in items
			])
		)

	def process_sequence(self, addresses, tree, node):
		chain = itertools.chain.from_iterable
		items = node[1]

		yield from self.serialization.prefixed('sequence', chain([
				self.serialization.prefixed('item', self.paragraph_content(addresses, tree, x[1]))
				for x in items
			])
		)

	def process_admonition(self, addresses, tree, content):
		assert content[0] == 'admonition'
		global itertools
		element = self.serialization.prefixed

		# both the key and the value are treated as paragraph data.
		severity, title = content[2]
		yield from element('admonition',
			self.process_section(addresses, tree, ('admonition-content', content[1])),
			('severity', severity),
		)

	def process_dictionary(self, addresses, tree, vl_node):
		assert vl_node[0] == 'dictionary'
		global itertools
		element = self.serialization.prefixed
		chain = itertools.chain.from_iterable

		# both the key and the value are treated as paragraph data.
		content = vl_node[1]

		keys = [element('key',
			chain([
				self.paragraph_index[part[0]](self, addresses, tree, *part[1:])
				for part in parts
			])) for parts in (x[1] for x in content[0::2])
		]

		values = [
			element('value', chain([self.process_section(addresses, tree, part)]))
			for part in content[1::2]
		]

		yield from element('dictionary',
			chain([element('item', chain(x)) for x in zip(keys, values)])
		)

	def paragraph_content(self, addresses, tree, sequence):
		global itertools

		if sequence:
			yield from itertools.chain.from_iterable([
				self.paragraph_index[part[0]](self, addresses, tree, *part[1:])
				for part in sequence
			])
		else:
			# empty paragraph
			pass

	def process_paragraph(self, addresses, tree, paragraph):
		global itertools

		if paragraph[1]:
			yield from self.serialization.prefixed('paragraph',
				itertools.chain.from_iterable([
					self.paragraph_index[part[0]](self, addresses, tree, *part[1:])
					for part in paragraph[1]
				])
			)
		else:
			# empty paragraph
			pass

	def process_subsection(self, addresses, tree, section):
		pass

	def process_literals(self, addresses, tree, sequence):
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

	section_index = {
		'paragraph': process_paragraph,
		'set': process_set,
		'sequence': process_sequence,
		'dictionary': process_dictionary,
		'section': process_subsection,
		'block': process_literals,
		'admonition': process_admonition,
	}

	def process_section(self, addresses, tree, section):
		assert section[0] in ('section', 'variable-content', 'admonition-content')
		for part in section[1]:
			yield from self.section_index[part[0]](self, addresses, tree, part)

	def serialize(self, addresses, tree):
		assert tree[0] == 'document'

		for section in tree[1]:
			if section[-1]:
				ident = libstring.normal(section[-1], separator='-')
			else:
				ident = None

			yield from self.serialization.prefixed('section',
				self.process_section(addresses, tree, section),
				('title', section[-1]),
				('xml:id', self.identify(ident) if ident is not None else None),
			)

	@classmethod
	def transform(Class, context:Context, prefix:str, source:str, encoding:str='utf-8', identify=lambda x: x):
		"""
		Construct an iterator producing XML from the given
		eclectic documentation &source.
		"""

		p = core.Parser()
		s = Class(context, libxml.Serialization(prefix, encoding), identify=identify)
		return s.serialize(*p.parse(source))
