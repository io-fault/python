"""
# Collection of data structures and functions for working with exact addresses in (syntax) text files.
"""
import typing
from ..computation import range as librange

class Address(tuple):
	"""
	# A Line Number and Column address used to identify a position in a syntax file.
	# Line numbers and columns are 1-based. There is no Line Zero and no column zero
	# with exception to Addresses used in &librange.IRange instances.

	# Address values must be constructed with one special condition:
	# if the address is being used in a range where the last character of the line
	# is being selected as the stop in the range,
	# the instance must be created to refer to the following line and the zero-column.
	# This special case is used to allow inclusive ranges to properly detect continuity.
	"""
	__slots__ = ()

	@classmethod
	def from_string(Class, source, Type=int, delimiter='.'):
		lineno, colno = source.split(delimiter, 1)
		return Class((Type(lineno), Type(colno)))

	def __str__(self):
		return "%s.%s"%(self[0], self[1])

	def __add__(self, x):
		return self.__class__((self[0], self[1]+x))

	def __sub__(self, x):
		return self.__class__((self[0], self[1]-x))

	def __mul__(self, x):
		return self.__class__((self[0]+x, self[1]))

	def __div__(self, x):
		return self.__class__((self[0]-x, self[1]))

	@property
	def line(self):
		"""
		# The line number identified by the address.

		# When the column number is zero, the internal value is adjusted under the
		# presumption that the address was referring to the end of the previos line.
		"""
		if self[1] == 0:
			return self[0] - 1
		else:
			return self[0]

	@property
	def column(self):
		"""
		# The column number identified by the address. &None if the address
		# is referring to the end of the &line.
		"""
		if self[1] == 0:
			return None
		else:
			return self[1]

	@staticmethod
	def normalize_stop(line_length, line_number, column_number):
		"""
		# Adjust a stop &Address' pointers for use in an &Area so that it can
		# be recognized as reference to the final character in a line.

		# If the given address points to the final position in the line, the line
		# number will be incremented and its column set to zero. This allows
		# &librange.Set to detect continuity when working with &Area instances.
		"""
		if column_number >= line_length:
			return line_number + 1, 0

		return line_number, column_number

class Area(librange.IRange):
	"""
	# Inclsuive Range of &Address instances. Usable with &librange.Set and
	# &librange.Mapping instances.
	"""
	Type = Address

	@classmethod
	def delineate(Class, lstart, cstart, lstop, cstop, stop_line_length):
		"""
		# Construct an &Area from the given indexes normalizing the stop address.
		"""

		lstop, cstop = Class.Type.normalize_stop(stop_line_length, lstop, cstop)
		return Area((Address((lstart,cstart)), Address((lstop,cstop))))

	@classmethod
	def from_string(Class, string, delimiter='-'):
		"""
		# Construct an &Area from the given string.
		"""

		seq = [
			Class((Class.Type.from_string(y[0]), Class.Type.from_string(y[1])))
			for y in (
				x.split(delimiter) for x in string.split()
			)
		]
		seq.sort()

		return Class.from_normalized_sequence(seq)

	def select(self, lines:typing.Sequence[typing.Text]):
		"""
		# Retrieve the prefix, suffix, and selected lines that are delieanted by the &Area, &self.
		"""

		lstart, cstart = self[0]
		lstop, cstop = self[1]
		if cstop == 0:
			lstop -= 1
			cstop = None

		subset = lines[lstart-1:lstop]

		# Divide the beginning and the end by the column start/stop.
		initial = subset[0]
		prefix = initial[:cstart-1]
		final = subset[-1]
		if cstop is None:
			suffix = ""
		else:
			suffix = final[cstop:]
			subset[-1] = final[:cstop]

		subset[0] = subset[0][cstart-1:]

		return prefix, suffix, subset
