"""
# Supplemental types.
"""

class Cell(object):
	"""
	# A Sequence implementation always containing a single element.

	# [ Engineering ]
	# The purpose of this type is to provide a means to allow receivers
	# of a sequence to know that the sequence produced in a particular case
	# will never contain more than one element without having to explicitly
	# communicate such a fact with another value sent alongside the sequence.

	# While an explicit plural field is clear and desirable, it also carries
	# the burden of having to be propagated with the sequence.
	# Having the sequence type designate the constraint allows the information
	# to be propagated without concern by the nodes along the call graph.
	"""
	__slots__ = ('element',)

	@classmethod
	def __setup__(Class):
		import collections.abc
		collections.abc.Sequence.register(Class)
		collections.abc.Iterable.register(Class)

	def coalesce(self, default, abscence=None):
		"""
		# Return the given &default if the element is &abscence.

		# By default, if the element is &None, return &default.
		"""
		if self.element is abscence:
			return default
		return self.element

	def __init__(self, element:object):
		self.element = element

	def __getitem__(self, index) -> object:
		if index != 0:
			raise IndexError("cell only contains a single element")

		return self.element

	def __iter__(self):
		yield self.element

	def __reversed__(self):
		return self

	def __len__(self) -> int:
		return 1

	def __eq__(self, operand) -> bool:
		if len(operand) != 1:
			return False
		return self.element == operand[0]

	def __contains__(self, item) -> bool:
		if item == self.element:
			return True
		return False

	def index(self, value, start=0, stop=None) -> int:
		if start != 0 or (stop is not None and stop <= 0):
			raise ValueError("range not present in cell")

		if value == self.element:
			return 0

		raise ValueError("cell element does not match the given value")

	def count(self, value) -> int:
		if value == self.element:
			return 1
		else:
			return 0

	def sort(self, key=None, reverse=False):
		"""
		# Sort the Cell's elements by doing nothing.
		"""
		pass
