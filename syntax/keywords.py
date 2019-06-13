"""
# Programming language profile and parser class for Keyword Oriented Syntax.

# Provides a data structure for describing keyword based languages that allows
# a naive processor to assign a classifications to the tokens contained
# by a string.

# &Profile instances have limited information regarding languages and &Parser instances should
# have naive processing algorithms. This intentional deficiency is a product of the goal to
# keep Keywords based interpretations trivial to implement and their parameter set small so that the
# the profile may be quickly and easily defined by users without requiring volumes of documentation.

# [ Engineering ]

# Essentially, this is a lexer whose tokens are defined by &Profile instances.
# The language types that are matches for applications are usually keyword based
# and leverage whitespace for isolation of fields.
"""
import typing
import itertools
import functools

from ..computation import string

class Profile(tuple):
	"""
	# Data structure describing the elements of a Keyword Oriented Syntax.

	# Empty strings present in any of these sets will usually refer to the End of Line.
	# This notation is primarily intended for area exclusions for supporting line comments,
	# but &literals and &enclosures may also use them to represent the beginning or end of a line.
	"""
	__slots__ = ()

	@classmethod
	def from_keywords_v1(Class,
			metawords=(),
			keywords=(),
			literals=(),
			exclusions=(),
			enclosures=(),
			routers=(),
			terminators=(),
			operations=(),
			corewords=(),
		):
		return Class(map(set, (
			metawords, keywords,
			literals,
			enclosures,
			terminators,
			routers,
			operations,

			exclusions, corewords,
		)))

	@property
	def metawords(self) -> typing.Set[str]:
		"""
		# Preprocessing directives commonly available to the language.
		# Used by C-like lanaguages, but limited to single forms. If the language
		# allows directive-words to be formatted in multiple ways, no
		# accommodation will be made by &Parser.
		"""
		return self[0]

	@property
	def keywords(self) -> typing.Set[str]:
		"""
		# Words reserved by the language.
		# This should normally be the union of keywords from all versions of the language.
		"""
		return self[1]

	@property
	def literals(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# The start and stop pairs delimiting a literal area within the syntax document.
		# Primarily used for string quotations, but supports distinct stops for
		# handling other cases as well.

		# Literals are given the highest priority by &Parser.
		"""
		return self[2]

	@property
	def exclusions(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# Comment start and stop pairs delimiting an excluded area from the source.

		# Exclusions are given the second highest priority by &Parser.
		"""
		return self[-2]

	@property
	def enclosures(self) -> typing.Set[typing.Tuple[str,str]]:
		"""
		# The start and stop pairs delimiting an expression.

		# Enclosures have the highest precedence during expression processing.
		"""
		return self[3]

	@property
	def terminators(self) -> typing.Set[str]:
		"""
		# Operators used to designate the end of a statement, expression, or field.
		"""
		return self[4]

	@property
	def routers(self) -> typing.Set[str]:
		"""
		# Operators used to designate a resolution path for selecting an object to be used.
		"""
		return self[5]

	@property
	def operations(self) -> typing.Set[str]:
		"""
		# Set of operators that can perform some manipulation to the objects associated
		# with the adjacent identifiers.
		"""
		return self[6]

	@property
	def corewords(self) -> typing.Set[str]:
		"""
		# Names of builtins used by the language.

		# This set of identifiers has the lowest precedence.
		"""
		return self[-1]

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
	# Keyword Oriented Syntax tokenization class.

	# Given a &Profile instance, a constructed instance will provide a
	# &tokenize method for processing syntax understood to match the profile.

	# [ Engineering ]

	# This is essentially a tightly coupled partial application for &tokenize.
	# &from_profile builds necessary parameters from a &Profile instance and
	# the internal constructor, &__init__, makes them available to the method.

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
		def classify_identifier(word, MW=profile.metawords, KW=profile.keywords, CW=profile.corewords):
			if word in KW:
				return 'keyword'
			elif word in CW:
				return 'coreword'
			elif word in MW:
				return 'metaword'
			else:
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

		return Class(
			profile,
			operators, opmap,
			delimiter, table,
			classify_identifier,
			classify_operators,
		)

	def __init__(self,
			profile,
			opset, opmap,
			delimiter, optable,
			classify_id,
			classify_op,
			spaces=" \t\n",
			opcachesize=32,
		):
		self.profile = profile

		self._spaces = spaces
		self._opset = opset
		self._opmap = opmap
		self._delimiter = delimiter
		self._optable = optable
		self._classify_id = classify_id
		self._classify_op = classify_op
		self._opcache = functools.lru_cache(opcachesize)(lambda x: list(classify_op(x)))

	def tokenize(self, line:str,
			len=len, zip=zip, list=list,
			varsplit=string.varsplit,
		) -> typing.Sequence[typing.Sequence[typing.Tuple[str,str,str]]]:
		"""
		# Token a string of syntax using the language profile given to a constructor.
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
