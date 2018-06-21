"""
# Text data structures for working with paragraph content.
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
	def type(self) -> str:
		"""
		# Type string of the fragment.
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
	# A sequenced of &Fragment instances forming a paragraph.
	"""
	__slots__ = ()

	def __repr__(self):
		return '%s(%s)' %(self.__class__.__name__, super().__repr__())

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
					current.append(QualifiedText(('text', parts[0]+'.')))
					yield current

					for p in parts[1:-1]:
						yield [QualifiedText(('text', p+'.'))]

					# New parts.
					current = [parts[-1]]
					continue

			# Sentence continued.
			current.append(x)
