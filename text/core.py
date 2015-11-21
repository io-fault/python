import itertools
import collections

from ..computation import library as libc
from ..computation import libstring

class Error(Exception):
	pass

class ContextError(Error):
	"""
	Context error.
	"""

class SyntaxError(Error):
	"""
	Eclectic syntax error. A tuple consisting of the line and the
	line number that produced an exception during processing.
	"""

class Parser(object):
	"""
	Configuration and state class for parsing eclectic markdown.

	[ Attributes ]

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

	def reference(self, string, punctuation='.;:,!-+?'):
		"""
		Split the string at the reference's boundary.
		The &string is presumed to be the start of a reference with
		the indicator removed.
		"""

		if string.startswith('<'):
			# Hyperlink/IRI
			ref = string[:string.find('>')+1]
		elif string:
			# Cross reference
			# Trailing punctuation is stripped.
			ref = string.split()[0].rstrip(punctuation)
		else:
			# empty string
			return ()

		return (('reference', ref), ('text', string[len(ref):]))

	def references(self, string, chain=itertools.chain.from_iterable):
		parts = string.split('&')

		# odds are text that have references
		# evens are plain text
		yield from chain(libc.interlace(
			[(('text', x),) for x in parts[0::2]],
			[self.reference(x) for x in parts[1::2]],
		))

	def styles(self, string):
		"""
		Identify the styles for the given string.
		"""
		yield from self.references(string)

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
				yield ('emphasis', e, start_count)
				if start_count != stop_count:
					raise ValueError("improperly balanced emphasis")

			if len(normal) > len(emphasized) and normal[-1]:
				yield ('text', normal[-1])

	def process_paragraph_line(self, code, il, line, chain=itertools.chain.from_iterable):
		"""
		Process a paragraph line identifying inline literals, references and emphasis.
		"""
		stripped = line.strip()

		if not stripped:
			# Whitespace. Paragraph break.
			yield ('paragraph-break', line)
		elif stripped and self.is_decoration(stripped):
			yield ('decoration', line)
		else:
			# inline code has the highest precedence, so
			# the initial split is performed on a backtick.
			parts = line.split('`')

			styled = list(chain(libc.interlace(
					map(tuple, map(self.styles, parts[0::2])),
					[(('literal', x),) for x in parts[1::2]],
				))
			)

			# Extract the casts modifying the following paragraph event.
			structure = []
			cast = None
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
							# not a cast
							structure.append(x)
						else:
							cast = x[1][start+1:-1]
							structure.append((x[0], x[1][:start]))
					else:
						# No processing necessary.
						structure.append(x)

			if structure[-1][0] == 'text':
				# Downstream's job is to remove trailing spaces from the paragraph.
				structure.append(('text', ' '))

			yield ('paragraph-line', structure)

	def process_literal_line(self, code, il, line):
		# reconstitute the original line
		# *relative* to the initial indentation
		yield ('literal-line', ((il - self.stack[-1][1]) * '\t') + line)

	def create_section(self, code, il, line):
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

		yield ('start-section', title.strip(), 1)

	def create_address(self, code, il, line):
		yield ('address', line.strip())

	def create_admonition(self, code, il, line):
		"""
		Lines that begin with "!":

		! NOTE:
			Paragraphs.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_paragraph_line, self.indentation, self.default_commands)

		severity, *title = line.strip().split(':', 1)
		yield ('descent', 'admonition',
			(severity, title and title[0] or None), self.indentation)
		yield ('enter-indentation-level', self.indentation)

	def create_block(self, code, il, line, commands={None:process_literal_line}):
		"""
		Code block of literal lines.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_literal_line, self.indentation, commands)

		yield ('descent', 'block', line, self.indentation)
		yield ('enter-indentation-level', self.indentation)

	def create_variable_item(self, code, il, line):
		if self.is_decoration(line):
			yield ('decoration', line)
		else:
			self.indentation = il + 1
			self.push(self.__class__.process_paragraph_line, self.indentation, self.default_commands)
			# variable list values are expected to descend.
			yield ('descent', 'variable-key',
				list(self.process_paragraph_line(code, il, line))[0][1], self.indentation)
			yield ('enter-indentation-level', self.indentation)

	def create_enumerated_item(self, code, il, line):
		if self.is_decoration(line):
			yield ('decoration', line)
		else:
			yield ('enumerated-item', list(self.process_paragraph_line(code, il, line))[0][1])

	def create_unordered_item(self, code, il, line):
		if self.is_decoration(line):
			yield ('decoration', line)
		else:
			yield ('unordered-item', list(self.process_paragraph_line(code, il, line))[0][1])

	def process(self, code, il, line):
		return self.stack[-1][0](self, code, il, line)

	default_commands = {
		'[': create_section,
		'@': create_address,
		'!': create_admonition,

		'/': create_variable_item,
		'-': create_unordered_item,
		'#': {
			None: create_enumerated_item,
			'!': create_block,
		},

		None: process,
	}

	def tokenize(self, lines:list):
		"""
		Tokenize the given source returning an iterator producing eclectic events.
		&source assumed to be is newline separated string.
		"""
		# essentially, this provides the basic paragraph formatting.

		for line, lineno in zip(lines, range(len(lines))):
			content = line.lstrip('\t')
			il = len(line) - len(content)

			if il > self.indentation:
				# identation increment detected.
				# anonymouse block quote
				oil = self.indentation
				self.indentation = il
				for x in range(oil+1, il+1):
					yield ('enter-indentation-level', x)
			elif il < self.indentation and line.strip() != '':
				for x in range(self.indentation, il, -1):
					yield ('exit-indentation-level', x)
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

			try:
				yield from command(self, command_code, il, content)
			except Exception as exc:
				raise SyntaxError((line, lineno)) from exc

	def structure(self, addresses, root, node, indentation, iterator):
		paragraph_content = {'paragraph', 'set-item', 'sequence-item'}
		# Every call represents an indentation level; anticipated or not.
		# Descent indicates a subgroup of nodes.
		ntype, subnodes, *nts = node

		for event, *params in iterator:
			# This should be a dictionary of operations like commands in tokenize.

			if event == 'paragraph-line':
				# extend existing paragraph or create new if it's not a paragraph
				if not subnodes or subnodes[-1][0] not in paragraph_content:
					subnodes.append(('paragraph', list(params[0])))
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
					subnodes.append(('paragraph', []))
			elif event == 'exit-indentation-level':
				# block is treated specially because it doesn't descend on indentation
				# events produced during the processing of literal-lines.
				assert params[0] > 0
				if ntype != 'block':
					break
				else:
					if indentation == params[0]:
						break

			elif event == 'enter-indentation-level':
				if params[0] != indentation and ntype != 'block':
					# if it didn't already push a structure() call from anticipated descent
					self.structure(addresses, root, node, params[-1], iterator)

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
			elif event == 'address':
				if subnodes:
					addresses[id(subnodes[-1])].add(params[0])
				else:
					addresses[id(node)].add(params[0])
			elif event == 'descent':
				# Essentially, these are a class of subsections.
				subtype, *params = params
				assert params[-1] > indentation

				if subtype == 'variable-key':
					if not subnodes or subnodes[-1][0] != 'dictionary':
						subnodes.append(('dictionary', []))
					subnodes[-1][1].append(('variable-key', params[0]))
					if params[0][-1][0] == 'text' and params[0][-1][1] == ' ':
						del params[0][-1]

					subnodes[-1][1].append(('variable-content', []))
					# anticipating indentation
					self.structure(addresses, root, subnodes[-1][1][-1], params[-1], iterator)
				elif subtype == 'block':
					subnodes.append((subtype, [], params[0]))
					self.structure(addresses, root, subnodes[-1], params[-1], iterator)
				elif subtype == 'admonition':
					admonition = (subtype, list(), params[0])
					subnodes.append(admonition)
					self.structure(addresses, root, admonition, params[-1], iterator)
			elif event == 'literal-line':
				if ntype != 'block':
					raise ValueError("literal line outside of block", event, params, indentation)
				subnodes.append(params[0])
			elif event == 'start-section':
				if indentation != 0:
					raise ValueError("section started inside indentation", event, params)
				else:
					# add a section node
					section = ('section', [], params[0])
					root[1].append(section)
					ntype, subnodes, *nts = node = section
			elif event == 'decoration':
				pass
			else:
				raise ValueError('unknown event type', event)
		else:
			# end of document as
			# exit-indentation-level causes breaks
			pass

	def parse(self, source:str, newline:str='\n'):
		"""
		Parse the source source into a tree structure.
		"""

		# Implicit section.
		addresses = collections.defaultdict(set)
		head = ('section', [('paragraph', [])], None) # initial section without title
		root = ('document', [head], None)

		self.structure(addresses, root, head, 0, self.tokenize(source.split(newline)))

		return addresses, root
