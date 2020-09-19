"""
# Abstract base classes for time measures and points.

# Primarily, this module exists to document the interfaces to &Point and &Measure.
# The redundant method declarations are intentional.

# ! WARNING:
	# There is some bitrot and conceptual conflicts.
	# &Range is likely misnamed and its role is not well clarified.
"""
import abc

class Time(metaclass=abc.ABCMeta):
	"""
	# The abstract base class for *all* Time related types.
	"""

class Range(Time):
	"""
	# The representation of the span between two quantities.

	# Often, time quantities are treated as ranges,
	# so make all time types ranges for practical purposes.
	"""

	@abc.abstractproperty
	def start(self):
		"""
		# The beginning of the range.
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		# The end of the range. Normally, &stop is treated in a non-inclusive manner.
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		# The size of the Range in terms of the &start.
		"""

	@abc.abstractmethod
	def __contains__(self, pit):
		"""
		# Determines whether or not the given `pit` is completely contained by the
		# Range.

		#!/syntax/python
			assert self.start >= pit and pit < self.stop
		"""

class Measure(Range):
	"""
	# An abstract quantity time. Usually, identified as a Scalar quantity unless
	# subclassed.
	"""

	@abc.abstractproperty
	def kind(self):
		"""
		# Classification for the unit type with respect to measurements.

		# Currently, only three kinds exist: definite, subjective, and indefinite.

		# Measures and Points of the same unit may have different unit kinds.
		"""

	@abc.abstractproperty
	def unit(self):
		"""
		# Identifier of the unit of time--usually the english name.

		# This *must* be a `str` where str(unit).isidentifier() is `True`.
		"""

	@abc.abstractproperty
	def name(self):
		"""
		# Name of the unit of time. Normally equal to
		# &Time.unit, but potentially different in cases
		# where the proper name is not an identifier.
		"""

	@abc.abstractproperty
	def start(self):
		"""
		# For Measure instances, this property *must* be zero.

		#!/syntax/python
			assert measure.start == 0
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		# For Measure instances, this property *must* be the instance, &self:

		#!/syntax/python
			assert measure.stop is measure
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		# The magnitude of the Time instance. For Measures, this is their integer value:

		#!/syntax/python
			assert int(measure) == measure.magnitude
		"""

	@abc.abstractclassmethod
	def of(Class, *times, **parts):
		"""
		# Create an instance of the type from the sum of the quantities
		# specified by &times and &parts:

		#!/syntax/python
			measure = Measure.of(hour = 33, microsecond = 44)

		# The above example only shows keyword use that is specific to the standard
		# time context used by &..time. Variable position arguments, &times,
		# must be pre-existing &Measure instances.

		# [ Parameters ]

		# /times/
			# A sequence of &Time instances.
		# /parts/
			# Keyword names designate the unit of the corresponding value.
			# The time context dictates what that is.
		"""

	@abc.abstractmethod
	def increase(self, *units, **parts):
		"""
		# Increase the measurement, repositioning the &stop.

		# Returns a new Measure instance whose value is `self` increased by
		# the given parameters.

		# This is equivalent to:

		#!/syntax/python
			assert self.increase(*units, **parts) == self.of(self, *units, **parts)

		# [ Parameters ]

		# /units/
			# Variable number of &Measure instances.
		# /parts/
			# Variable keywords whose keys designate the unit.
		"""

	@abc.abstractmethod
	def decrease(self, *units, **parts):
		"""
		# Decrease the measurement, repositioning the &stop.

		# Returns a new Measure instance whose value is `self` decreased by
		# the given parameters.

		# This is equivalent to:

		#!/syntax/python
			neg_units = [-unit for unit in units]
			neg_parts = {k:-v for (k,v) in parts}

			assert self.decrease(*units, **parts) == self.of(self, *neg_units, **neg_parts)

		# [ Parameters ]

		# /units/
			# Variable number of &Measure instances.
		# /parts/
			# Variable keywords whose keys designate the unit.
		"""

	@abc.abstractmethod
	def select(self, part, of = None, align = 0):
		"""
		# Extract the number of complete parts designated by `part` after the last
		# complete whole, `of`, with respect to the alignment, `align`.

		# The result is an &int or an arbitrary object given that
		# a Container part is referenced.

		# Common cases:

		#!/syntax/python
			h = x.select('hour', 'day')
			m = x.select('minute', 'hour')
			s = x.select('second', 'minute')
			u = x.select('microsecond', 'second')

		# [ Parameters ]

		# /part/
			# The unit whose count is to be returned.
		# /of/
			# The unit whose total wholes are subtracted
			# from `self` in order to find the correct total parts.
		# /align/
			# How to align the given part.
			# Trivially, this is a difference that is applied
			# prior to removing wholes: `value = self - align`.
		"""

	@abc.abstractmethod
	def update(self, part, replacement, of = None, align = 0):
		"""
		# Construct and return a new instance adjusted by the difference between the
		# selected part and the given value with respect to the specified alignment.

		# The following holds true:

		#!/syntax/python
			updated = pit.update(part, replacement, of, align)
			adjusted = this.adjust(**{part: replacement - pit.select(part, of, align)})
			assert updated == adjusted

		# It's existence as an interface is due to its utility.

		# [ Parameters ]

		# /part/
			# The name of the Part unit to set.
		# /replacement/
			# The new value to set.
		# /of/
			# The name of the Whole unit that defines the boundary of the part.
		# /align/
			# Defaults to zero; the adjustment applied to the boundary.
		"""

	@abc.abstractmethod
	def truncate(self, unit):
		"""
		# Truncates the time instance to the specified boundary: remove units smaller
		# than the given &unit.

		# [ Parameters ]

		# /unit/
			# The minimum unit size to allow in the new time instance.
		"""

class Point(Range):
	"""
	# A Point in Time; a &Range relative to an understood datum.
	# Points isolate a position in time *with* a mangitude of one unit.
	# The purpose of the &Range superclass is primarily practical as allowing
	# &.types.Date instances to be perceived as the span of
	# the entire day is frequently useful.
	"""

	@abc.abstractproperty
	def kind(self):
		"""
		# Classification for the unit type with respect to Points in Time.
		"""

	@abc.abstractproperty
	def Measure(self) -> Measure:
		"""
		# The Point's corresponding scalar class used to measure deltas.
		# This provides access to a &Measure whose precision is consistent with the &Point.

		# [ Invariants ]
		#!/syntax/python
			assert point.Measure.unit == point.unit
			assert issubclass(point.Measure, Measure)
		"""

	@abc.abstractproperty
	def start(self):
		"""
		# Points *must* return the instance, &self:

		# [ Invariants ]
		#!/syntax/python
			assert point.start is point
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		# The next Point according to the unit:

		# [ Invariants ]
		#!/syntax/python
			assert point.stop == point.elapse(point.Measure(1))
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		# The magnitude of the Point. For Points, this *must* be one::

		#!/syntax/python
			assert pit.magnitude == 1
		"""

	@abc.abstractmethod
	def measure(self, pit):
		"""
		# Return the measurement, &Measure instance, between &self and
		# the given point in time, &pit. The delta between the two points.
		"""

	@abc.abstractmethod
	def elapse(self, *units, **parts):
		"""
		# Returns an adjusted measure in time by the given arguments and keywords.

		# Essentially, this is a call to the &of
		# method with the instance as the first parameter.

		# This is shorthand for `t.of(t, *units, **parts)`.
		"""

	@abc.abstractmethod
	def rollback(self, *units, **parts):
		"""
		# The point in time that occurred the given number of units before this
		# point. The semantics are identical to &Point.elapse, but transforms
		# the parameters into negative values.

		# [ Invariants ]

		#!/syntax/python
			pit == (pit.rollback(*measures, **units)).elapse(*measures, **units)
		"""

	@abc.abstractmethod
	def leads(self, pit):
		"""
		# Returns whether or not the Point in Time, self,
		# comes *before* the given argument, &pit.
		"""

	@abc.abstractmethod
	def follows(self, pit):
		"""
		# Returns whether or not the Point in Time, self,
		# comes *after* the given argument, &pit.
		"""
