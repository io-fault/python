"""
# Programming language profile and parser class for Keyword Oriented Syntax.

# Provides a data structure for describing keyword based languages that allows
# a naive processor to assign classifications to the tokens contained
# by a string.

# &Profile instances have limited information regarding languages and &Parser instances should
# have naive processing algorithms. This intentional deficiency is a product of the goal to
# keep Keywords based interpretations trivial to implement and their parameter set small so that the
# the profile may be quickly and easily defined by users without requiring volumes of documentation
# to be consumed.

# [ Parser Process Methods ]

# &Parser instances have two high-level methods for producing tokens: &Parser.process_lines and
# &Parser.process_document. The former resets the context provided to &Parser.delimit for each line,
# and the latter maintains it throughout the lifetime of the generator.

# While &Parser.process_document appears desireable in many cases, the limitations of &Profile instances
# may make it reasonable to choose &Parser.process_lines in order to avoid the effects of an
# inaccruate profile or a language that maintains ambiguities with respect to the parser's capabilities.

# [ Engineering ]

# Essentially, this is a lexer whose tokens are defined by &Profile instances.
# The language types that are matches for applications are usually keyword based
# and leverage whitespace for isolation of fields.
"""
import typing
import itertools
import functools

from ..context import string

Tokens = typing.Iterable[typing.Tuple[str,str,str]]

class Profile(tuple):
	"""
	# Data structure describing the elements of a Keyword Oriented Syntax.

	# Empty strings present in any of these sets will usually refer to the End of Line.
	# This notation is primarily intended for area exclusions for supporting line comments,
	# but &literals and &enclosures may also use them to represent the beginning or end of a line.

	# While &Profile is a tuple subclass, indexes should *not* be used to access members.
	"""
	__slots__ = ()

	@classmethod
	def from_keywords_v1(Class,
			exclusions=(),
			literals=(),
			enclosures=(),
			routers=(),
			operations=(),
			terminators=(),
			**wordtypes
		):
		fields = list(map(set, (
			map(tuple, exclusions),
			map(tuple, literals),
			map(tuple, enclosures),
			routers,
			operations,
			terminators,
		)))
		fields.append({k:set(v) for k, v in wordtypes.items()})
		return Class(fields)

	@property
	def words(self) -> typing.Mapping[str, typing.Set[str]]:
		"""
		# Dictionary associating sets of identifier strings with a classification identifier.
		"""
		return self[-1]

	@property
	def exclusions(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# Comment start and stop pairs delimiting an excluded area from the source.

		# Exclusions are given the second highest priority by &Parser.
		"""
		return self[0]

	@property
	def literals(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# The start and stop pairs delimiting a literal area within the syntax document.
		# Primarily used for string quotations, but supports distinct stops for
		# handling other cases as well.

		# Literals are given the highest priority by &Parser.
		"""
		return self[1]

	@property
	def enclosures(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# The start and stop pairs delimiting an expression.

		# Enclosures have the highest precedence during expression processing.
		"""
		return self[2]

	@property
	def routers(self) -> typing.Set[str]:
		"""
		# Operators used to designate a resolution path for selecting an object to be used.
		"""
		return self[3]

	@property
	def operations(self) -> typing.Set[str]:
		"""
		# Set of operators that can perform some manipulation to the objects associated
		# with the adjacent identifiers.
		"""
		return self[4]

	@property
	def terminators(self) -> typing.Set[str]:
		"""
		# Operators used to designate the end of a statement, expression, or field.
		"""
		return self[5]

	@property
	def operators(self) -> typing.Iterable[str]:
		"""
		# Emit all unit operators employed by the language associated with a rank and context effect.
		# Operators may appears multiple times. Empty strings represent end of line.

		# Operators are emitted by their classification in the following order:
			# # Operations
			# # Routers
			# # Terminators
			# # Enclosures
			# # Literals
			# # Exclusions

		# Order is deliberate in order to allow mappings to be directly built so
		# later classes will overwrite earlier entries in cases of ambiguity.
		"""

		yield from (('operation', 'event', x) for x in self.operations)
		yield from (('router', 'event', x) for x in self.routers)
		yield from (('terminator', 'event', x) for x in self.terminators)

		for x in self.enclosures:
			if x[0] == x[1]:
				yield ('enclosure', 'delimit', x[0])
			else:
				yield ('enclosure', 'start', x[0])
				yield ('enclosure', 'stop', x[1])

		for x in self.literals:
			if x[0] == x[1]:
				yield ('literal', 'delimit', x[0])
			else:
				yield ('literal', 'start', x[0])
				yield ('literal', 'stop', x[1])

		for x in self.exclusions:
			if x[0] == x[1]:
				yield ('exclusion', 'delimit', x[0])
			else:
				yield ('exclusion', 'start', x[0])
				yield ('exclusion', 'stop', x[1])

class Parser(object):
	"""
	# Keyword Oriented Syntax parser providing tokenization and region delimiting.

	# Instances do not hold state and methods of the same instance may be used
	# by multiple threads.

	# [ Engineering ]

	# This is essentially a tightly coupled partial application for &tokenize
	# and &delimit. &from_profile builds necessary parameters using a &Profile
	# instance and the internal constructor, &__init__, makes them available to the methods.

	# Applications should create and cache an instance for a given language.
	"""

	@classmethod
	def from_profile(Class, profile:Profile):
		"""
		# Primary constructor for &Parser.

		# Instances should usually be cached when repeat use is expected as
		# some amount of preparation is performed by &from_profile.
		"""

		# Identifier classification
		def classify_identifier(word, wtypes=profile.words):
			for typid, wordset in wtypes.items():
				if word in wordset:
					return typid

			return 'identifier'

		# Assign integer identities for multi-character tokens and end-of-line.
		opmap = {x[-1]: x for x in profile.operators}
		opmap.pop('', None)

		opmaxread = max(map(len, opmap))
		opminread = min(map(len, opmap)) or 1

		# Select a translation target for the operator set.
		delimiter = min((len(x), x) for x in opmap if x)[1]
		operators = set(itertools.chain.from_iterable(opmap))
		table = str.maketrans({x:delimiter for x in operators})

		def classify_operators(opchars, opclasses=opmap, opmin=opminread, opmax=opmaxread):
			"""
			# Interpret operators in the string &opchars according to their classification
			# specified in &opclasses.

			# [ Engineering ]
			# Uses simple backtracking to find the greatest possible match
			# from left to right. If no match is found, the operator will be classified
			# as `'fragment'`.
			"""
			area = opmax

			while opchars:
				op = opchars[:area]

				if op in opclasses:
					yield opclasses[op]
					opchars = opchars[area:]
					area = opmax
				else:
					# No maximum match, backtrack.
					area -= 1
					if area < opmin:
						yield ('fragment', 'event', op)
						opchars = opchars[opmin:]
						area = opmax

		exits = {}
		for ops in (profile.enclosures, profile.exclusions, profile.literals):
			exits.update({x[0]: x[1] for x in ops if x[0] != x[1]})

		return Class(
			profile,
			operators, opmap,
			delimiter, table, exits,
			classify_identifier,
			classify_operators,
		)

	def __init__(self,
			profile,
			opset, opmap,
			delimiter, optable, exits,
			classify_id,
			classify_op,
			spaces=" \t\n",
			opcachesize=32,
		):
		"""
		# ! WARNING: Do not use directly.
			# The initializer's parameters are subject to change.
			# &from_profile should be used to build instances.
		"""
		self.profile = profile

		self._spaces = spaces
		self._opset = opset
		self._opmap = opmap
		self._delimiter = delimiter
		self._optable = optable
		self._exits = exits
		self._classify_id = classify_id
		self._classify_op = classify_op
		self._opcache = functools.lru_cache(opcachesize)(lambda x: list(classify_op(x)))

	def process_lines(self, lines:typing.Iterable[str], eol='\n') -> typing.Iterable[typing.Iterable[Tokens]]:
		"""
		# Process lines using context resets;
		# &tokenize and &delimit multiple &lines resetting the context at the end of each line.

		# This is the recommended method for extracting tokens from a file for syntax documents
		# that are expected to restate line context, have inaccurate profiles, or are incomplete.

		# The produced iterators may be ran out of order as no parsing state is shared across lines.
		"""

		tok = self.tokenize
		delimit = self.delimit

		for line in lines:
			yield delimit([('inclusion', None)], tok(line), eol=eol)

	def process_document(self, lines:typing.Iterable[str], eol='\n') -> typing.Iterable[typing.Iterable[Tokens]]:
		"""
		# Process lines of a complete source code file using continuous context;
		# &tokenize and &delimit multiple lines maintaining the context across all &lines.

		# This is the recommended method for extracting tokens from a file for syntax documents
		# that are expected to *not* restate line context *and* have accurate profiles.

		# The produced iterators **must** be ran in the produced order as the context is shared across
		# instances.
		"""

		ctx = self.allocstack()
		tok = self.tokenize
		delimit = self.delimit

		for line in lines:
			yield delimit(ctx, tok(line), eol=eol)

	def allocstack(self):
		"""
		# Allocate context stack for use with &delimit.
		"""
		return [('inclusion', None)]

	def delimit(self, context, tokens:Tokens, eol='\n', restate=True) -> Tokens:
		"""
		# Insert switch tokens into an iteration of tokens marking the
		# boundaries of expressions, comments and quotations.

		# &context is manipulated during the iteration and maintains the
		# nested state of comments. &allocstack may be used to allocate an
		# initial state.

		# This is a relatively low-level method; &process_lines or &process_document
		# should normally be used.
		"""

		ctx_id, ctx_exit = context[-1]
		get_exit = self._exits.get

		previous = ('switch', ctx_id, '')
		if restate:
			# Only state initial ground or explicitly requested.
			yield previous

		for t in tokens:
			t_type, t_qual, t_chars = t

			if t_qual not in {'start', 'stop', 'delimit'} or t_type == 'enclosure':
				if ctx_exit == '' and t_type == 'space' and eol in t_chars:
					# Handle End of Line exits specially.
					context.pop()
					yield ('switch', context[-1][0], '')

					while context[-1][1] == '':
						context.pop()
						yield ('switch', context[-1][0], '')

					ctx_id, ctx_exit = context[-1]

				yield t
			else:
				assert t_qual in {'start', 'stop', 'delimit'}
				exit_match = (t_chars == ctx_exit)

				# Translate delimit to start/stop.
				if t_qual == 'delimit':
					if exit_match:
						# Might Pop
						effect = False
					else:
						# Might Push
						effect = True
				else:
					effect = (t_qual == 'start')

				if effect:
					# maybe push and switch to new
					new_exit = get_exit(t_chars, t_chars)

					if ctx_id == 'inclusion' or (ctx_id == t_type and new_exit == ctx_exit):
						# Ground state or the token was consistent.
						ctx_id = t_type
						ctx_exit = new_exit
						context.append((ctx_id, ctx_exit))
						yield ('switch', ctx_id, '')
						yield (t_type, 'start', t_chars)
					else:
						yield t
				elif exit_match and ctx_id == t_type:
					# pop and switch to old

					context.pop()
					ctx_id, ctx_exit = context[-1]
					yield (t_type, 'stop', t_chars)
					yield ('switch', ctx_id, '')
				else:
					yield t

			previous = t

	def tokenize(self, line:str,
			len=len, zip=zip, list=list,
			varsplit=string.varsplit,
		) -> Tokens:
		"""
		# Tokenize a string of syntax according to the profile.

		# Direct use of this is not recommended as boundaries are not signalled.
		# &process_lines or &process_document should be used.
		# The raw tokens, however, are usable in contexts where boundary information is
		# not desired or is not accurate enough for an application's use.
		"""

		areas = list(varsplit(self._delimiter, line.translate(self._optable)))

		classify_id = self._classify_id
		classify_op = self._classify_op
		offset = 0

		area_ids = areas[0::2]
		area_ops = areas[1::2]
		area_ops.append(0)

		for identifier, opcount in zip(area_ids, area_ops):
			idlen = len(identifier)
			ops = len(identifier) + offset
			end = ops + opcount

			opchars = line[ops:end]
			offset = end

			trailing = 0
			iid = identifier.strip()

			if idlen != len(iid):
				# Emit leading spaces, if any.
				leading = identifier[:identifier.find(iid[:1])]
				if leading:
					yield ('space', 'lead', leading)
					trailing = idlen - (len(leading) + len(iid))
				else:
					trailing = idlen - len(iid)

			# Not pure whitespace.
			foffset = 0
			noffset = 0
			for field in iid.split():
				noffset = iid.find(field[:1], foffset)
				assert noffset != -1

				if foffset != noffset:
					yield ('space', 'pad', iid[foffset:noffset])
				foffset = noffset + len(field)

				yield (classify_id(field), 'event', field)

			if trailing != 0:
				# Emit trailing spaces.
				yield ('space', 'follow', identifier[-trailing:])

			# Single unambiguous entry?
			if opchars in self._opmap:
				yield self._opmap[opchars]
				continue
			else:
				# not a single/simple recognized token.
				yield from self._opcache(opchars)
