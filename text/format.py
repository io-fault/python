"""
# Parser implementation and supporting tools for the fault-text format.

# The parser is hand rolled in order to easily accommodate for grammar
# violations, and as an attempt to display the format's simplicity. While the
# tokenizer enjoys an easily understood implementation, syntactic analysis
# (&Parser.structure) is hacked and nearly unreadable demanding a replacement.

# [ Types ]

# /Tree/
	# The element tree produced by &Parser processing operations.

# [ Engineering ]
# The current implementation of the parser failed to achieve a desired level
# of simplicity. While it usually produces the desired result, the lack of
# implementation coherency should result in a rewrite.
"""

from collections.abc import Sequence, Mapping
import builtins
import itertools

from ..context import string
from ..context import tools

# The element tree produced by parsing a document.
Tree = tuple[str, Sequence['Tree'], Mapping]

def parse_section_selector(string:str) -> tuple[int, Sequence[str]]:
	"""
	# Given the contents of a section command or reference,
	# return the depth and the section path specified within the
	# given &string.
	"""
	shift_level = None
	sl_multiple = None
	rtitle = string.split(' ', 1)

	if rtitle[0][:1] == ">":
		# Relative
		remainder = rtitle[0].replace('>', '')
		shift_level = len(rtitle[0]) - len(remainder)
		if remainder:
			sl_multiple = int(remainder) # Malformed Relative Section

		if len(rtitle) == 1 or rtitle[-1] == "":
			path = ()
		else:
			path = tuple(map(str.strip, rtitle[-1].split(" >> ")))
	else:
		path = tuple(map(str.strip, string.split(" >> ")))

	return (shift_level, sl_multiple, path)

# This iterator exists solely for the purpose of handling
# transitions from set/sequence items to another type.
class Tokens(object):
	"""
	# Iterator that allows events to be replayed in order for them
	# to be processed by the appropriate context.
	"""
	__slots__ = ('iterators',)

	def __init__(self, iterator):
		self.iterators = [iter(iterator)]

	def replay(self, *events):
		self.iterators.insert(0, iter(events))

	def __iter__(self):
		return self

	def __next__(self):
		its = self.iterators
		while its:
			for x in its[0]:
				return x
			else:
				del its[0]
		else:
			raise StopIteration

class Parser(object):
	"""
	# Configuration and state class for parsing kleptic text.

	# [ Properties ]
	# /stack/
		# The stack of line processing callbacks for the given context.
	# /paragraph/
		# A sequence representing the current working paragraph.
	# /indentation/
		# The current indentation level.
	# /path/
		# The current section path.
	# /prefix/
		# The designated bottom of the &path.
		# Used to allow subchapter tokens to be introduced as an extension
		# of the root chapter.
	"""

	def __init__(self):
		"""
		# Create a new parser instance initializing the &stack with the &default_commands,
		# and &process_paragraph_line as the means to process lines.
		"""
		self.stack = [(self.__class__.process_paragraph_line, 0, self.default_commands)]
		self.indentation = 0
		self.path = ()
		self.prefix = 0

	@property
	def commands(self):
		"""
		# Return the set of commands for the current working processor.
		"""
		return self.stack[-1][-1]

	def reference(self, string,
			punctuation=',.;:-+!?()[]{}',
			terminators=str.maketrans({i:'\n' for i in ' \t()[]{}'})
		):
		"""
		# Split the string at the reference's boundary.
		# The &string is presumed to be the start of a reference with
		# the indicator removed.

		#!text
			# &<...>
			# &[Parameters(...)]
			# (int *)`3928+23192-203`
		"""
		label = None

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
				# Wasteful as only the first match needs to be checked.
				r = string.translate(terminators).split('\n', 1)[0]

				# Lines are tokens, so newlines are safe tokens to use.
				# Also, we'd stop on a newline anyways.
				ref = r.rstrip(punctuation)
			else:
				ref = ''
			typ = 'normal'

		return (('reference', ref, typ, label, action), ('text', string[len(ref):]))

	@property
	def processor(self):
		"""
		# The current processing method, command set, and indentation level.
		# Top of the &stack.
		"""
		return self.stack[-1]

	def push(self, proc, il, command_set):
		self.stack.append((proc, il, command_set))

	def pop(self):
		del self.stack[-1]

	def is_decoration(self, stripped, minimum=5, level=3, allowed=set("-=_^#><'+*")):
		"""
		# Determine if the line is a decoration.
		"""
		sl = len(stripped)
		chars = set(stripped)
		nc = len(chars)

		if sl >= minimum and nc >= 1 and nc <= level and not (chars - allowed):
			return True

		return False

	@staticmethod
	def emphasis(text, *, indicator='*', varsplit=string.varsplit):
		"""
		# Return a sequence of paragraph events noting the emphasis areas versus
		# regular text.
		"""

		list=builtins.list
		zip=builtins.zip
		len=builtins.len

		parts = list(varsplit(indicator, text))
		texts = parts[0::2]
		counts = parts[1::2]
		if not counts:
			yield ('text', texts[0])
		else:
			normal = texts[0::2]
			emphasized = texts[1::2]
			pairs = list(zip(counts[0::2], counts[1::2]))
			if len(pairs) < len(normal):
				pairs.append((counts[-1], 0))

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

	def styles(self, string:str, edge:bool=True,
			reference_indicator='&',
			chain=itertools.chain.from_iterable
		):
		"""
		# Identify the styles and references for the given string.

		# [ Parameters ]
		# /string/
			# The text between a literal area.
		# /edge/
			# Whether the &string was on the edge of a literal.
		"""
		trail = None
		rcontent = string

		if edge and string.endswith(')'):
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
		# Structure the paragraph line revealing emphasis,
		# references, and inline literals.
		"""
		# inline literals have the highest precedence, so
		# the initial split is performed on a grave accent.
		parts = line.split('`')

		styled = list(chain(tools.interlace(
				map(tuple, map(self.styles, parts[0:-1:2])),
				[(('literal', x),) for x in parts[1::2]],
			))
		)
		if len(parts) % 2 == 1:
			styled.extend(self.styles(parts[-1], edge=False))

		# Extract the casts modifying the following paragraph event.
		structure = []
		cast = None
		previous = None
		for x in styled:
			if cast is not None:
				structure.append(x + (cast,))
				cast = None
			else:
				typ = x[0]
				txt = x[1]

				if typ != 'text':
					structure.append(x)
					continue

				if txt.endswith(')'):
					start = txt.rfind('(')
					if start != -1:
						cast = txt[start+1:-1]
						txt = txt[:start]

				if txt.count('*') > 1:
					structure.extend(self.emphasis(txt))
				else:
					structure.append((typ, txt) + x[2:])
		else:
			if cast is not None:
				# cast at the end of the paragraph-line
				# replace the partial state with the correct text entry
				structure[-1] = x

		return structure

	def process_paragraph_line(self, lineno, code, il, line):
		"""
		# Process a paragraph line identifying inline literals, references and emphasis.
		"""
		stripped = line.strip()

		if not stripped:
			# Whitespace. Paragraph break.
			yield (lineno, 'paragraph-break', [('text', line)])
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
			yield (lineno, 'warning',
				"section commands should end with an equal number of closing brackets")

		title = title.strip() # Strip title content.

		if not title:
			yield (lineno, 'select-section', (None, None, ()))
		else:
			yield (lineno, 'select-section', parse_section_selector(title))

	def create_admonition(self, lineno, code, il, line):
		"""
		# Lines that begin with "!":

		#!text
			" ! NOTE:
				" Paragraphs.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_paragraph_line, self.indentation, self.default_commands)

		severity, *title = line.strip().split(':', 1)
		yield (lineno, 'descent', 'admonition',
			(severity, title and title[0] or None), self.indentation)
		yield (lineno, 'enter-indentation-level', self.indentation)

	def create_block(self, lineno, code, il, line, commands={None:process_literal_line}):
		"""
		# Code block of literal lines.
		"""

		self.indentation = il + 1
		self.push(self.__class__.process_literal_line, self.indentation, commands)

		yield (lineno, 'descent', 'syntax', line, self.indentation)
		yield (lineno, 'enter-indentation-level', self.indentation)

	def create_variable_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			self.indentation = il + 1
			# variable list values are expected to descend.
			if line.endswith('/'):
				line = line[:-1]
				syntax_type = None
			else:
				# Check for syntax value.
				parts = line.rsplit('/#!', 1)
				if len(parts) > 1:
					line, syntax_type = parts
				else:
					del parts
					syntax_type = None

			yield (lineno, 'descent', 'variable-key',
				list(self.process_paragraph_line(lineno, code, il, line))[0][2], self.indentation)
			yield (lineno, 'enter-indentation-level', self.indentation)

			if syntax_type is None:
				self.push(
					self.__class__.process_paragraph_line,
					self.indentation, self.default_commands
				)
			else:
				commands = {None:self.__class__.process_literal_line}
				self.push(self.__class__.process_literal_line, self.indentation, commands)
				yield (lineno, 'key-syntax', syntax_type, self.indentation)

	def create_enumerated_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			parts = list(self.process_paragraph_line(lineno, code, il, line))
			yield (lineno, 'enumerated-item', parts[0][2])

	def create_unordered_item(self, lineno, code, il, line):
		if self.is_decoration(line):
			yield (lineno, 'decoration', line)
		else:
			parts = list(self.process_paragraph_line(lineno, code, il, line))
			yield (lineno, 'unordered-item', parts[0][2])

	def process(self, lineno, code, il, line):
		return self.stack[-1][0](self, lineno, code, il, line)

	default_commands = {
		'[': select_section,
		'!': create_admonition,

		'/': create_variable_item,
		'-': create_unordered_item,
		'#': {
			# Sequence Item
			None: create_enumerated_item,
			# Syntax Area / Block Quote
			'!': create_block,
		},

		None: process,
	}

	def tokenize(self, lines:Sequence[str]):
		"""
		# Tokenize the given source returning an iterator producing text events.
		# &source presumed to be is newline separated string.
		"""

		# essentially, this provides the basic paragraph formatting.
		if lines and lines[0].startswith('#!'):
			# Initial #! is treated specially for the shebang.
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
				# Indentation increment detected.
				# Anonymous block quote.
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

			# Identify the line's purpose.
			command_code = ''
			command = self.commands
			while command.__class__ is dict:
				if content and content[0] in command:
					# Commands are subjected to decoration tests.
					command = command[content[0]]
					command_code += content[0]
					content = content[1:]
				else:
					# Continuation of existing context; usually paragraph.
					command = command[None]

			yield from command(self, lineno, command_code, il, content)

	def process(self, sections, root, element, indentation, iterator):
		# Stack depth is proportional to the indentation level.
		paragraph_content = {'paragraph'}
		ntype = element[0]
		subelements = element[1]

		for token in iterator:
			# This should be a dictionary of operations like commands in tokenize.
			line, event, *params = token
			if subelements:
				context = subelements[-1]
				context_type = context[0] if context else None
			else:
				context = None
				context_type = None

			if event == 'paragraph-line':
				# extend existing paragraph or create new if it's not a paragraph
				if not subelements or subelements[-1][0] not in paragraph_content:
					if ntype in {'set', 'sequence'}:
						if element[-1] == indentation:
							# Indentation at the subject element's level.
							# Handle the case following an exit inside
							# a set or sequence.
							iterator.replay(token)
							break
						else:
							subelements[-1][1][-1][1].extend(params[0])
					else:
						content = list(params[0])
						content.append(('eol', ''))
						subelements.append(('paragraph', content, indentation))
				else:
					subelements[-1][1].extend(params[0])

			elif event in ('paragraph-break', 'decoration') or (
					(event, ntype) in {
						('unordered-item', 'sequence'),
						('enumerated-item', 'set'),
					}
				):
				# Explicit break; empty paragraphs will be ignored downstream.
				if ntype in {'set', 'sequence'}:
					# Clear trailing whitespace before processing
					# the next item.
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][:2] == ('text', ' '):
						del trailing[-1]
					# Handle unindented process() descent performed by set.
					if event in ('unordered-item', 'enumerated-item'):
						iterator.replay(token)
					break

				# Actual paragraph break.
				if subelements and subelements[-1][0] in paragraph_content:
					if not subelements[-1][1]:
						# Don't add entries if it's already on an empty paragraph.
						continue
					else:
						# The tokenizer appends text whitespace at the end of each
						# paragraph line in order to provide proper spacing.
						# However, it doesn't peek ahead in order to inhibit spaces
						# at the end of a paragraph, so filter it here.
						trailing = subelements[-1][1]
						trim = None
						for i in range(-1, -(len(trailing) + 1), -1):
							if trailing[i] == ('eol', ''):
								continue
							if trailing[i] == ('text', ' '):
								trim = i
								break
						if trim is not None:
							del trailing[trim]

				if not subelements or subelements[-1][0] in paragraph_content:
					# it only needs to break inside paragraphs.
					if subelements:
						subelements[-1][1].append(('eol', ''))

					# Prepare a new paragraph.
					subelements.append(('paragraph', [('init', '')], None))
			elif event == 'exit-indentation-level':
				# block is treated specially because it doesn't descend on indentation
				# events produced during the processing of literal-lines.

				assert params[0] > 0 # indentation always > 0 on exit

				if ntype == 'variable-content' and subelements and subelements[-1] and subelements[-1][1]:
					# Trim implicitly created paragraphs.
					paras = subelements[-1]
					if paras[1][-1] == ('eol', ''):
						empty_addr = -2
					else:
						empty_addr = -1
					if paras[1][empty_addr] == ('text', ' '):
						del paras[1][empty_addr]

				if ntype != 'syntax':
					return True
				else:
					if indentation == params[0]:
						# Leave the process() call representing
						# the indentation level.
						return True
					else:
						# Don't leave loop if IL > indentation.
						# For blocks, this allows literals to continue
						# to be identified as part of the element.
						pass

			elif event == 'enter-indentation-level':
				if ntype in {'set', 'sequence'}:
					# Jump into the current working item on enter.
					self.process(sections, root, subelements[-1], params[-1], iterator)
					# Exit processed inside call.

				elif params[0] != indentation and ntype != 'syntax':
					# if it didn't already push a process() call from anticipated descent
					if subelements and subelements[-1][0] == 'paragraph':
						# Uninitialized paragraph start.
						para = subelements[-1]
						if len(para) > 2 and para[2] is None:
							subelements[-1] = (para[0], para[1], params[-1])

					self.process(sections, root, element, params[-1], iterator)
					# Exit processed.

			elif event == 'unordered-item':
				if ntype in {'sequence'}:
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

					iterator.replay(token)
					return False

				if ntype != 'set':
					element = (
						'set', [
							('set-item', [('paragraph', list(params[0]))])
						],
						params[-1]
					)
					subelements.append(element)

					if self.process(sections, root, element, indentation, iterator):
						break
				else:
					# Remove trailing paragraph content from previous entry.
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

					subelements.append((
						'set-item', [
							('paragraph', list(params[0]))
						]
					))

			elif event == 'enumerated-item':
				if ntype in {'set'}:
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

					iterator.replay(token)
					return False

				# Processed exactly as unordered-item.
				if ntype != 'sequence':
					element = (
						'sequence', [
							('sequence-item', [('paragraph', list(params[0]))])
						],
						params[-1]
					)
					subelements.append(element)

					if self.process(sections, root, element, indentation, iterator):
						break
				else:
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

					subelements.append((
						'sequence-item', [
							('paragraph', list(params[0]))
						]
					))

			elif event == 'descent':
				# variable-key (/)
				# block (#!)
				# admonition (!)
				# Descent is the name of the token as they
				# share the property of having an expectation
				# that the next line will be indented.

				if ntype in {'set', 'sequence'}:
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

					# Pop set/sequence state and replay token in parent context.
					# set and sequence unconditionally descend.
					iterator.replay(token)
					return False

				# Essentially, these are a class of subsections.
				subtype, *params = params

				# Indentation of the token *must* be greater
				# than that of the working element as the exit
				# events should have been present and processed
				# otherwise.
				assert params[-1] > indentation

				if subtype == 'variable-key':
					il = params[-1] # il of key

					if not subelements or subelements[-1][0] not in {'dictionary', 'directory'}:
						# New directory and new current working element.
						subelements.append(('directory', [], params[-1]))
					else:
						# Current subelement is a directory.
						# If indentation is greater, it's
						# inside the outer directory's indentation level,
						# so it's a new dictioanry.
						if il > subelements[-1][-1]:
							# il of key is greater than the current target element.
							subelements.append(('directory', [], params[-1]))

					dn = subelements[-1]
					dn_content = dn[1]
					dn_content.append(('variable-key', params[0]))

					if params[0][-1] == ('text', ' '):
						del params[0][-1]

					dn_content.append(('variable-content', [], indentation))
					self.process(sections, root, dn_content[-1], params[-1], iterator)
					# after variable-content
				elif subtype == 'syntax':
					block = (subtype, [], params[0])
					subelements.append(block)
					self.process(sections, root, block, params[-1], iterator)
				elif subtype == 'admonition':
					admonition = (subtype, [], params[0])
					subelements.append(admonition)
					self.process(sections, root, admonition, params[-1], iterator)
			elif event == 'literal-line':
				if ntype != 'syntax':
					subelements.append(('exception', (),
						"literal line outside of block", event, line, indentation, params))
				else:
					subelements.append(params[0])
			elif event == 'key-syntax':
				block = ('syntax', [], params[0])
				subelements.append(block)
				element = block
				ntype = 'syntax'
				subelements = block[1]
			elif event == 'select-section':
				if ntype in {'set', 'sequence'}:
					trailing = subelements[-1][1][-1][1]
					if trailing and trailing[-1][0] == 'text' and trailing[-1][1] == ' ':
						del trailing[-1]

				if indentation != 0:
					subelements.append(('exception', (),
						"section selected inside indentation",
						event, line, indentation, params))
				else:
					# create or re-use a section
					sl, sl_m, spath = params[0]
					segment = (sl or 0) * (1 if sl_m is None else 1)
					prefix = self.path[self.prefix:self.prefix+segment]
					title = prefix + spath

					if title in sections:
						section = sections[title]
					else:
						section = ('section', [], (title, sl, sl_m, spath))
						sections[title] = section
						if len(title) > 1:
							sections[title[:-1]][1].append(section)
						else:
							root[1].append(section)

					self.path = title

					# switch to the new section context
					element = section
					ntype = element[0]
					subelements = element[1]
			elif event == 'decoration':
				pass
			else:
				subelements.append(('exception', (),
					"unknown event type",
					event, line, indentation, params))

			# end of switch
		else:
			# end of document as
			# exit-indentation-level causes breaks
			pass

	def structure(self, lines:Sequence[str]) -> Tree:
		"""
		# Structure the given &lines into an element tree.
		"""

		# Implicit section.
		root = ('chapter', [('paragraph', [], None)], {})

		tokens = self.tokenize(lines)
		ctx = next(tokens)
		self.process(dict([((), root)]), root, root, 0, Tokens(tokens))

		return root

	def parse(self, source:str, newline:str='\n') -> Tree:
		"""
		# Parse the source source into a tree structure.
		"""
		return self.structure(source.split(newline))
