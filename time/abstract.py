"""
# Abstract base classes for time measures and points.

# Primarily, this module exists to document the interfaces to &Point and &Measure.
# The redundant method declarations are intentional.
"""
from abc import abstractmethod, abstractclassmethod
import typing

class Time(typing.Protocol):
	"""
	# The abstract base class for *all* Time related types.
	"""

	@property
	@abstractmethod
	def start(self):
		"""
		# The beginning of the range. Inclusive.
		"""

	@property
	@abstractmethod
	def stop(self):
		"""
		# The end of the range. Exclusive.
		"""

	@property
	@abstractmethod
	def magnitude(self):
		"""
		# The size of the range in terms of the &start.
		"""

	@abstractmethod
	def __contains__(self, pit):
		"""
		# Whether the given point falls between &start, inclusive, and &stop, exclusive.

		#!python
			assert self.start >= pit and pit < self.stop
		"""

	@abstractclassmethod
	def of(Class, *times, **parts):
		"""
		# Create an instance of the type from the sum of the quantities
		# specified by &times and &parts:

		#!python
			t = Time.of(hour = 33, microsecond = 44)

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

	@abstractmethod
	def select(self, part, of=None, align=0):
		"""
		# Extract the number of complete parts designated by `part` after the last
		# complete whole, `of`, with respect to the alignment, `align`.

		# The result is an &int or an arbitrary object given that
		# a Container part is referenced.

		# Common cases:

		#!python
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

	@abstractmethod
	def update(self, part, replacement, of=None, align=0):
		"""
		# Construct and return a new instance adjusted by the difference between the
		# selected part and the given value with respect to the specified alignment.

		# The following holds true:

		#!python
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

	@abstractmethod
	def truncate(self, unit):
		"""
		# Truncates the time instance to the specified boundary: remove units smaller
		# than the given &unit.

		# [ Parameters ]
		# /unit/
			# The minimum unit size to allow in the new time instance.
		"""

class Measure(Time):
	"""
	# An abstract quantity time. Usually, identified as a Scalar quantity unless
	# subclassed.
	"""

	@property
	@abstractmethod
	def kind(self):
		"""
		# Classification for the unit type with respect to measurements.

		# Currently, only three kinds exist: definite, subjective, and indefinite.

		# Measures and Points of the same unit may have different unit kinds.
		"""

	@property
	@abstractmethod
	def unit(self):
		"""
		# Identifier of the unit of time--usually the english name.

		# This *must* be a `str` where str(unit).isidentifier() is `True`.
		"""

	@property
	@abstractmethod
	def name(self):
		"""
		# Name of the unit of time. Normally equal to
		# &Time.unit, but potentially different in cases
		# where the proper name is not an identifier.
		"""

	@property
	@abstractmethod
	def start(self):
		"""
		# For Measure instances, this property *must* be zero.

		#!python
			assert measure.start == 0
		"""

	@property
	@abstractmethod
	def stop(self):
		"""
		# For Measure instances, this property *must* be the instance, &self:

		#!python
			assert measure.stop is measure
		"""

	@property
	@abstractmethod
	def magnitude(self):
		"""
		# The magnitude of the Time instance. For Measures, this is their integer value:

		#!python
			assert int(measure) == measure.magnitude
		"""

	@abstractmethod
	def increase(self, *units, **parts):
		"""
		# Increase the measurement, repositioning the &stop.

		# Returns a new Measure instance whose value is `self` increased by
		# the given parameters.

		# This is equivalent to:

		#!python
			assert self.increase(*units, **parts) == self.of(self, *units, **parts)

		# [ Parameters ]
		# /units/
			# Variable number of &Measure instances.
		# /parts/
			# Variable keywords whose keys designate the unit.
		"""

	@abstractmethod
	def decrease(self, *units, **parts):
		"""
		# Decrease the measurement, repositioning the &stop.

		# Returns a new Measure instance whose value is `self` decreased by
		# the given parameters.

		# This is equivalent to:

		#!python
			neg_units = [-unit for unit in units]
			neg_parts = {k:-v for (k,v) in parts}

			assert self.decrease(*units, **parts) == self.of(self, *neg_units, **neg_parts)

		# [ Parameters ]
		# /units/
			# Variable number of &Measure instances.
		# /parts/
			# Variable keywords whose keys designate the unit.
		"""

class Point(Time):
	"""
	# A point in time.
	"""

	@property
	@abstractmethod
	def kind(self):
		"""
		# Classification for the unit type with respect to Points in Time.
		"""

	@property
	@abstractmethod
	def Measure(self) -> typing.Type[Measure]:
		"""
		# The Point's corresponding scalar class used to measure deltas.
		# This provides access to a &.abstract.Measure whose precision is consistent with the &Point.

		# [ Invariants ]
		#!python
			assert point.Measure.unit == point.unit
		"""

	@property
	@abstractmethod
	def start(self):
		"""
		# Points *must* return the instance, &self:

		# [ Invariants ]
		#!python
			assert point.start is point
		"""

	@property
	@abstractmethod
	def stop(self):
		"""
		# The next Point according to the unit:

		# [ Invariants ]
		#!python
			assert point.stop == point.elapse(point.Measure(1))
		"""

	@property
	@abstractmethod
	def magnitude(self):
		"""
		# The magnitude of the Point. For Points, this *must* be one:

		#!python
			assert pit.magnitude == 1
		"""

	@abstractmethod
	def measure(self, pit):
		"""
		# Return the measurement, &Measure instance, between &self and
		# the given point in time, &pit. The delta between the two points.
		"""

	@abstractmethod
	def elapse(self, *units, **parts):
		"""
		# Returns an adjusted measure in time by the given arguments and keywords.

		# Essentially, this is a call to the &of
		# method with the instance as the first parameter.

		# This is shorthand for `t.of(t, *units, **parts)`.
		"""

	@abstractmethod
	def rollback(self, *units, **parts):
		"""
		# The point in time that occurred the given number of units before this
		# point. The semantics are identical to &Point.elapse, but transforms
		# the parameters into negative values.

		# [ Invariants ]
		#!python
			pit == (pit.rollback(*measures, **units)).elapse(*measures, **units)
		"""

	@abstractmethod
	def leads(self, pit):
		"""
		# Returns whether or not the Point in Time, self,
		# comes *before* the given argument, &pit.
		"""

	@abstractmethod
	def follows(self, pit):
		"""
		# Returns whether or not the Point in Time, self,
		# comes *after* the given argument, &pit.
		"""
