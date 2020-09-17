"""
# Text data structures for working with paragraph content.

# &Fragment and &Paragraph are designed to be easily transformed and serialized
# using common tools. &Fragment *should* always be a pair-tuple, and &Paragraph a
# sequence of Fragments. The JSON/msgpack representation would likely be
# a sequence of sequences or a pair of sequences to be recombined.

# These text structure primitives are not ideal for managing fine grained formatting
# control. They are intended for managing semantic markup. However, &Fragment
# being arbitrarily typed allows for format control events that could be interpreted
# by a Processing Context for such a purpose.
"""
import typing

class Fragment(tuple):
	"""
	# An explicitly typed portion of text used as part of a &Paragraph.
	"""
	__slots__ = ()

	@property
	def typepath(self) -> typing.Sequence[str]:
		return self[0].split('/', 3)

	@property
	def data(self) -> str:
		return self[1]

	@property
	def emphasis(self) -> int:
		"""
		# Return the integer weight of the emphasized text.
		# &None if the text is not emphasized.
		"""
		tp = self.typepath
		if tp[:2] != ('text', 'emphasis'):
			return None

		return int(self.typepath[2])

	@property
	def type(self) -> str:
		"""
		# Type string of the fragment.

		# Usually a (character)`/` separated string where the first two fields
		# are supposed to exist unconditionally. Common prefixes:

		# - (id)`text/normal`
		# - (id)`text/emphasis/[0-9]*`
		# - (id)`reference/hyperlink`
		# - (id)`referance/section`
		# - (id)`reference/ambiguous`
		# - (id)`reference/parenthetical`
		# - (id)`literal/grave-accent`
		"""
		return self[0]

	@property
	def root(self) -> str:
		"""
		# Initial path entry. Usually `reference`, `literal`, or `text`.
		"""
		return self.typepath[0]

	@classmethod
	def new(Class, type, data):
		"""
		# Create a new instance with an explicitly declared type.
		"""
		return Class((type, data))

class Paragraph(list):
	"""
	# A sequence of &Fragment instances forming a paragraph.
	"""
	__slots__ = ()

	def __repr__(self):
		return '%s(%s)' %(self.__class__.__name__, super().__repr__())

	@classmethod
	def of(Class, *sequence:Fragment):
		"""
		# Variable argument based &Paragraph constructor.
		"""
		return Class(sequence)

	@property
	def sole(self) -> Fragment:
		"""
		# Return the first and only fragment of the Paragraph.
		# If multiple fragments exist, a &ValueError is raised.
		"""
		only_fragment, = self
		return only_fragment

	@property
	def sentences(self):
		"""
		# Iterator producing lists that contain the sentence contents.
		# A sentence in a paragraph is delimited by (character)`.` contained
		# within `'text'`
		"""

		current = []
		for x in self:
			if x[0] == 'text':
				parts = x[1].split('.')
				if len(parts) > 1:
					# Terminate sentence.
					current.append(Fragment(('text', parts[0]+'.')))
					yield current

					for p in parts[1:-1]:
						yield [Fragment(('text', p+'.'))]

					# New parts.
					if parts[-1]:
						current = [Fragment(('text', parts[-1]))]
					else:
						current = []
					continue
			else:
				current.append(x)

		if current:
			yield current
