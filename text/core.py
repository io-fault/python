import itertools
import collections

from ..computation import library as libc
from ..computation import libstring

from typing import Sequence

class Error(Exception):
	pass

class SyntaxError(Error):
	"""
	Eclectic syntax error. A tuple consisting of the line and the
	line number that produced an exception during processing.
	"""

class Parser(object):
	"""
	Configuration and state class for parsing eclectic markdown.

	[ Properties ]

	/stack
		...
	/paragraph
		A sequence representing the current working paragraph.
	/indentation
		The current indentation level.
	"""

	def __init__(self):
		"""
		Create a new parser instance.
		"""
		self.stack = [(self.__class__.process_paragraph_line, 0, self.default_commands)]
		self.indentation = 0

	@property
	def commands(self):
		"Return the set of commands for the current working processor."
		return self.stack[-1][-1]

	def reference(self,
			string,
			punctuation=',.;:!-+?()[]{}',
		):
		"""
		Split the string at the reference's boundary.
		The &string is presumed to be the start of a reference with
		the indicator removed.

		#!text
			&*<...>
			&*[Parameters(...)]
			(int *)`3928+23192-203`
		"""
		substruct = ()

		if string.startswith('*'):
			string = string[1:]
			action = 'include'
		else:
			action = None

		if string.startswith('<'):
			# Hyperlink/IRI
			ref = string[:string.find('>')+1]
			typ = 'hyperlink'
		elif string.startswith('['):
			ref = string[:string.find(']')+1]
			typ = 'section'
		else:
			# Cross reference
			# Trailing punctuation is stripped.
			if string:
				ref = string.split()[0].rstrip(punctuation)
			else:
				ref = ''
			typ = 'normal'

		label = None

		return (('reference', ref, typ, label, action), ('text', string[len(ref):]))

	@property
	def processor(self):
		"""
		The current processing method, command set, and indentation level.
		Top of the &stack.
		"""
		return self.stack[-1]

	def push(self, proc, il, command_set):
		self.stack.append((proc, il, command_set))

	def pop(self):
		del self.stack[-1]

	def is_decoration(self, stripped, minimum=4, level=3):
		"Determine if the line is a decoration."
		sl = len(stripped)
		chars = set(stripped)
		nc = len(chars)

		if sl > minimum and nc >= 1 and nc <= level:
			return True

		return False

	@staticmethod
	def emphasis(text, indicator='*', varsplit=libstring.varsplit):
		"""
		Return a sequence of paragraph events noting the emphasis areas versus regular
		text.
		"""

		parts = list(varsplit(indicator, text))
		texts = parts[0::2]
		counts = parts[1::2]
		if not counts:
			yield ('text', texts[0])
		else:
			normal = texts[0::2]
			emphasized = texts[1::2]
			pairs = zip(counts[0::2], counts[1::2])

			for n, e, (start_count, stop_count) in zip(normal, emphasized, pairs):
				yield ('text', n)
				if start_count == stop_count:
					yield ('emphasis', e, start_count)
				else:
					# yield ('warning', 'unbalanced emphasis')
					yield ('text', start_count*'*')
					yield ('text', e)
					yield ('text', stop_count*'*')

			if len(normal) > len(emphasized) and normal[-1]:
				yield ('text', normal[-1])

	def styles(self, string:str,
			reference_indicator='&',
			chain=itertools.chain.from_iterable
		):
		"""
		Identify the styles and references for the given string.
		"""
		trail = None
		rcontent = string

		if string.endswith(')'):
			cast_open = string.rfind('(')
			if cast_open > -1:
				# Skip cast content.
				rcontent = string[:cast_open]
				trail = string[cast_open:]

		txt, *refs = rcontent.split('&')
		yield ('text', txt)
		yield from chain(self.reference(x) for x in refs)
		if trail is not None:
			yield ('text', trail)

	def structure_paragraph_line(self, line, chain=itertools.chain.from_iterable):
		"""
		Structure the paragraph line revealing emphasis,
		references, and inline literals.
		"""
		# inline literals have the highest precedence, so
		# the initial split is performed on a grave accent.
		parts = line.split('`')

		styled = list(chain(libc.interlace(
				map(tuple, map(self.styles, parts[0::2])),
				[(('literal', x),) for x in parts[1::2]],
			))
		)

		# Extract the casts modifying the following paragraph event.
		structure = []
		cast = None
		previous = None
		for x in styled:
			if cast is not None:
				structure.append(x + (cast,))
				cast = None
			else:
				if x[0] == 'text' and x[1].count('*') > 1:
					structure.extend(self.emphasis(x[1]))
					continue

				if x[0] == 'text' and x[1].endswith(')'):
					start = x[1].rfind('(')

					if start == -1:
						# Not a cast.
						structure.append(x)
					else:
						cast = x[1][start+1:-1]
						structure.append((x[0], x[1][:start]))
				else:
					# No processing necessary.
					structure.append(x)
		else:
			if cast is not None:
				# cast at the end of the paragraph-line
				# replace the partial state with the correct text entry
				structure[-1] = x

		return structure

	def process_paragraph_line(self, lineno, code, il, line):
		"""
		Process a paragraph line identifying inline literals, references and emphasis.
		"""
		stripped = line.strip()

		if not stripped:
			# Whitespace. Paragraph break.
			yield (lineno, 'paragraph-break', line)
		elif stripped and self.is_decoration(stripped):
			yield (lineno, 'decoration', line)
		else:
			structure = self.structure_paragraph_line(stripped)
			if structure:
				# Downstream's job is to remove trailing spaces from the paragraph.
				structure.append(('text', ' '))

			yield (lineno, 'paragraph-line', structure)

	def process_literal_line(self, lineno, code, il, line):
		# reconstitute the original line
		# *relative* to the initial indentation
		yield (lineno, 'literal-line', ((il - self.stack[-1][1]) * '\t') + line)

	def select_section(self, lineno, code, il, line):
		base = line.strip()
		bl = len(base)
		prefix = base.rstrip(']')
		title = prefix.lstrip('[')

		tail_length = bl - len(prefix)
		head_length = (bl - tail_length) - len(title)

		# The check adds one to head_length because the command resolution
		# process strips the command code character.
		if tail_length != (head_length + 1):
			raise ValueError("section commands must end with an equal number of closing brackets")

		if title:
			path = tuple(map(str.strip, title.split('>>')))
		else:
			path = ()

		yield (lineno, 'select-section', path, 1)

	def create_directive(self, lineno, code, il, line):
		yield (lineno, 'directive', line.strip())

	def create_admonition(self, lineno, code, il, line):
		"""
		Lines that begin with "!":

		! NOTE:
			Paragraphs.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_paragraph_line, self.indentation, self.default_commands)

		severity, *title = line.strip().split(':', 1)
		yield (lineno, 'descent', 'admonition',
			(severity, title and title[0] or None), self.indentation)
		yield (lineno, 'enter-indentation-level', self.indentation)

	def create_block(self, lineno, code, il, line, commands={None:process_literal_line}):
		"""
		Code block of literal lines.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_literal_line, self.indentation, commands)

		yield (lineno, 'descent', 'block', line, self.indentation)
		yield (lineno, 'enter-indentation-level', self.indentation)

	def create_variable_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			self.indentation = il + 1
			self.push(self.__class__.process_paragraph_line, self.indentation, self.default_commands)
			# variable list values are expected to descend.
			yield (lineno, 'descent', 'variable-key',
				list(self.process_paragraph_line(lineno, code, il, line))[0][2], self.indentation)
			yield (lineno, 'enter-indentation-level', self.indentation)

	def create_enumerated_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			yield (lineno, 'enumerated-item', list(self.process_paragraph_line(lineno, code, il, line))[0][2])

	def create_unordered_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			yield (lineno, 'unordered-item', list(self.process_paragraph_line(lineno, code, il, line))[0][2])

	def process(self, lineno, code, il, line):
		return self.stack[-1][0](self, lineno, code, il, line)

	default_commands = {
		'[': select_section,
		'@': create_directive,
		'!': create_admonition,

		'/': create_variable_item,
		'-': create_unordered_item,
		'#': {
			None: create_enumerated_item,
			'!': create_block,
		},

		None: process,
	}

	def tokenize(self, lines:Sequence[str]):
		"""
		Tokenize the given source returning an iterator producing eclectic events.
		&source assumed to be is newline separated string.
		"""

		# essentially, this provides the basic paragraph formatting.
		if lines[0].startswith('#!'):
			# initial #! is treated specially for title
			yield (1, 'context', lines[0].split(' ', 2))
			start = 1
		else:
			yield (0, 'context', None)
			start = 0

		lslice = itertools.islice(lines, start, None)
		for line, lineno in zip(lslice, range(start+1, len(lines)+1)):
			content = line.lstrip('\t')
			il = len(line) - len(content)

			if il > self.indentation:
				# identation increment detected.
				# anonymouse block quote
				oil = self.indentation
				self.indentation = il
				for x in range(oil+1, il+1):
					yield (lineno, 'enter-indentation-level', x)
			elif il < self.indentation and line.strip() != '':
				for x in range(self.indentation, il, -1):
					yield (lineno, 'exit-indentation-level', x)
					if self.stack[-1][1] == x:
						# if the current stack entry is
						# bound to the il, pop it.
						self.pop()
				self.indentation = il

			# identify the line's purpose
			command_code = ''
			command = self.commands
			while command.__class__ is dict:
				if content and content[0] in command:
					# commands are subjected to decoration tests.
					command = command[content[0]]
					command_code += content[0]
					content = content[1:]
				else:
					# continuation of existing context; usually paragraph
					command = command[None]

			# Parsing exceptions need to be reported as tokens.
			yield from command(self, lineno, command_code, il, content)

	def structure(self, sections, root, node, indentation, iterator):
		paragraph_content = {'paragraph', 'set-item', 'sequence-item'}
		# Every call represents an indentation level; anticipated or not.
		# Descent indicates a subgroup of nodes.
		ntype, subnodes, *nts = node

		for token in iterator:
			# This should be a dictionary of operations like commands in tokenize.
			line, event, *params = token

			if event == 'paragraph-line':
				# extend existing paragraph or create new if it's not a paragraph
				if not subnodes or subnodes[-1][0] not in paragraph_content:
					content = list(params[0])
					content.append(('eol', ''))
					subnodes.append(('paragraph', content))
				else:
					subnodes[-1][1].extend(params[0])
			elif event in ('paragraph-break', 'decoration'):
				# Explicit break; empty paragraphs will be ignored downstream.
				if subnodes and subnodes[-1][0] in paragraph_content:
					if not subnodes[-1][1]:
						# Don't add entries if it's already on an empty paragraph.
						continue
					else:
						# The tokenizer appends text whitespace at the end of each
						# paragraph line in order to provide proper spacing.
						# However, it doesn't peek ahead in order to inhibit spaces
						# at the end of a paragraph, so filter it here.
						trailing = subnodes[-1][1]
						if trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
							del trailing[-1]

				if not subnodes or subnodes[-1][0] == 'paragraph':
					# it only needs to break inside paragraphs.
					if subnodes:
						subnodes[-1][1].append(('eol', ''))
					subnodes.append(('paragraph', []))
			elif event == 'exit-indentation-level':
				# block is treated specially because it doesn't descend on indentation
				# events produced during the processing of literal-lines.
				assert params[0] > 0

				if ntype != 'block':
					break
				else:
					if indentation == params[0]:
						# leave the structure() call representing
						# the indentation level.
						break

			elif event == 'enter-indentation-level':
				if params[0] != indentation and ntype != 'block':
					# if it didn't already push a structure() call from anticipated descent
					self.structure(sections, root, node, params[-1], iterator)

			elif event == 'unordered-item':
				if ntype != 'set':
					# it's expecting to be in an indentation,
					# thus an inner structure() call, so it can overwrite
					# the current state until the indentation exits
					# restoring the outer node.
					node = ('set', [])
					subnodes.append(node)
					ntype, subnodes, *nts = node
					subnodes.append(('set-item', list(params[0])))
				else:
					subnodes.append(('set-item', list(params[0])))
			elif event == 'enumerated-item':
				# processed exactly as unordered-item.
				if ntype != 'sequence':
					node = ('sequence', [])
					subnodes.append(node)
					ntype, subnodes, *nts = node
					subnodes.append(('sequence-item', list(params[0])))
				else:
					subnodes.append(('sequence-item', list(params[0])))
			elif event == 'directive':
				# enqueue for the following object.
				if subnodes[-1][0] != 'break':
					subnodes.append(('break', ()))
			elif event == 'descent':
				# Essentially, these are a class of subsections.
				subtype, *params = params
				assert params[-1] > indentation

				if subtype == 'variable-key':
					if not subnodes or subnodes[-1][0] != 'dictionary':
						subnodes.append(('dictionary', [], indentation))
					dn = subnodes[-1]
					dn_content = dn[1]
					dn_content.append(('variable-key', params[0]))

					if params[0][-1][0] == 'text' and params[0][-1][1] == ' ':
						del params[0][-1]

					dn_content.append(('variable-content', [], indentation))
					# anticipating indentation
					self.structure(sections, root, dn_content[-1], params[-1], iterator)
					# after variable-content
				elif subtype == 'block':
					subnodes.append((subtype, [], params[0]))
					self.structure(sections, root, subnodes[-1], params[-1], iterator)
				elif subtype == 'admonition':
					admonition = (subtype, list(), params[0])
					subnodes.append(admonition)
					self.structure(sections, root, admonition, params[-1], iterator)
			elif event == 'literal-line':
				if ntype != 'block':
					subnodes.append(('exception', (),
						"literal line outside of block", event, lineno, indentation, params))
				else:
					subnodes.append(params[0])
			elif event == 'select-section':
				if indentation != 0:
					subnodes.append(('exception', (),
						"section selected inside indentation",
						event, lineno, indentation, params))
				else:
					# create or re-use a section
					title = params[0] # tuple consisting of title path

					if title in sections:
						section = sections[title]
					else:
						section = ('section', [], title)
						sections[title] = section
						if len(title) > 1:
							sections[title[:-1]][1].append(section)
						else:
							root[1].append(section)

					# switch to the new section context
					ntype, subnodes, *nts = node = section
			elif event == 'decoration':
				pass
			else:
				subnodes.append(('exception', (),
					"unknown event type",
					event, lineno, indentation, params))
		else:
			# end of document as
			# exit-indentation-level causes breaks
			pass

	def parse(self,
			source:str, newline:str='\n',
			dictionary=collections.defaultdict,
			set=set,
		):
		"""
		Parse the source source into a tree structure.
		"""

		# Implicit section.
		head = ('section', [('paragraph', [])], None) # initial section without title
		root = ('document', [head], None)

		tokens = self.tokenize(source.split(newline))
		ctx = next(tokens)
		self.structure(dict(), root, head, 0, tokens)

		return root
