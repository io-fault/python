"""
Abstract base classes for time measures and points.

The inheritance hierarchy can get messy. These ABCs help to keep the inheritance
under control and provide easy access to the APIs.
"""
import abc

class Time(metaclass=abc.ABCMeta):
	"""
	The abstract base class for *all* Time related types.
	"""

class Range(Time):
	"""
	The representation of the span between two quantities.

	Often, time quantities are treated as ranges,
	so make all time types ranges for practical purposes.
	"""

	@abc.abstractproperty
	def start(self):
		"""
		The beginning of the range.
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		The end of the range. Normally, &stop is treated in a non-inclusive manner.
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The size of the Range in terms of the &start.
		"""

	@abc.abstractmethod
	def __contains__(self, pit):
		"""
		Determines whether or not the given `pit` is completely contained by the
		Range.

		#!/pl/python
			assert self.start >= pit and pit < self.stop
		"""

class Measure(Range):
	"""
	An abstract quantity time. Usually, identified as a Scalar quantity unless
	subclassed.
	"""

	@abc.abstractproperty
	def kind(self):
		"""
		Classification for the unit type with respect to measurements.

		Currently, only three kinds exist: definite, subjective, and indefinite.

		Measures and Points of the same unit may have different unit kinds.
		"""

	@abc.abstractproperty
	def unit(self):
		"""
		Identifier of the unit of time--usually the english name.

		This *must* be a `str` where str(unit).isidentifier() is `True`.
		"""

	@abc.abstractproperty
	def name(self):
		"""
		Name of the unit of time. Normally equal to
		&Time.unit, but potentially different in cases
		where the proper name is not an identifier.
		"""

	@abc.abstractproperty
	def start(self):
		"""
		For Measure instances, this property *must* be zero.

		#!/pl/python
			assert measure.start == 0
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		For Measure instances, this property *must* be the instance, &self:

		#!/pl/python
			assert measure.stop is measure
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The magnitude of the Time instance. For Measures, this is their integer value:

		#!/pl/python
			assert int(measure) == measure.magnitude
		"""

	@abc.abstractclassmethod
	def of(Class, *times, **parts):
		"""
		Create an instance of the type from the sum of the quantities
		specified by &times and &parts:

		#!/pl/python
			measure = Measure.of(hour = 33, microsecond = 44)

		The above example only shows keyword use that is specific to the standard
		time context used by Chronometry. Variable position arguments, &times,
		are pre-existing &Measure instances.

		[ Parameters ]

		/&times
			A sequence of &Time instances.
		/&parts
			Keyword names designate the unit of the corresponding value.
			The time context dictates what that is.
		"""

	@abc.abstractmethod
	def increase(self, *units, **parts):
		"""
		Increase the measurement, repositioning the &stop.

		Returns a new Measure instance whose value is `self` increased by
		the given parameters.

		This is equivalent to:

		#!/pl/python
			assert self.increase(*units, **parts) == self.of(self, *units, **parts)

		[ Parameters ]

		/&units
			Variable number of &Measure instances.
		/&parts
			Variable keywords whose keys designate the unit.
		"""

	@abc.abstractmethod
	def decrease(self, *units, **parts):
		"""
		Decrease the measurement, repositioning the &stop.

		Returns a new Measure instance whose value is `self` decreased by
		the given parameters.

		This is equivalent to:

		#!/pl/python
			neg_units = [-unit for unit in units]
			neg_parts = {k:-v for (k,v) in parts}

			assert self.decrease(*units, **parts) == self.of(self, *neg_units, **neg_parts)

		[ Parameters ]

		/&units
			Variable number of &Measure instances.
		/&parts
			Variable keywords whose keys designate the unit.
		"""

	@abc.abstractmethod
	def select(self, part, of = None, align = 0):
		"""
		Extract the number of complete parts designated by `part` after the last
		complete whole, `of`, with respect to the alignment, `align`.

		The result is an &int or an arbitrary object given that
		a Container part is referenced.

		Common cases:

		#!/pl/python
			h = x.select('hour', 'day')
			m = x.select('minute', 'hour')
			s = x.select('second', 'minute')
			u = x.select('microsecond', 'second')

		[ Parameters ]

		/&part
			The unit whose count is to be returned.
		/&of
			The unit whose total wholes are subtracted
			from `self` in order to find the correct total parts.
		/&align
			How to align the given part.
			Trivially, this is a difference that is applied
			prior to removing wholes: `value = self - align`.
		"""

	@abc.abstractmethod
	def update(self, part, replacement, of = None, align = 0):
		"""
		Construct and return a new instance adjusted by the difference between the
		selected part and the given value with respect to the specified alignment.

		The following holds true:

		#!/pl/python
			updated = pit.update(part, replacement, of, align)
			adjusted = this.adjust(**{part: replacement - pit.select(part, of, align)})
			assert updated == adjusted

		It's existence as an interface is due to its utility.

		[ Parameters ]

		/&part
			The name of the Part unit to set.
		/&replacement
			The new value to set.
		/&of
			The name of the Whole unit that defines the boundary of the part.
		/&align
			Defaults to zero; the adjustment applied to the boundary.
		"""

	@abc.abstractmethod
	def truncate(self, unit):
		"""
		Truncates the time instance to the specified boundary: remove units smaller
		than the given &unit.

		[ Parameters ]

		/&unit
			The minimum unit size to allow in the new time instance.
		"""

class Point(Range):
	"""
	A Point in Time; a &Range relative to an understood datum.
	Points isolate a position in time *with* a mangitude of one unit.
	The purpose of the &Range superclass is primarily practical as allowing
	&.library.Date instances to be perceived as the span of
	the entire day is frequently useful.
	"""

	@abc.abstractproperty
	def kind(self):
		"""
		Classification for the unit type with respect to Points in Time.
		"""

	@abc.abstractproperty
	def Measure(self):
		"""
		The Point's corresponding scalar class used to measure deltas.
		This provides access to a &Measure with consistent precision.

		[ Invariants ]
		#!/pl/python
			assert point.Measure.unit == point.unit
			assert issubclass(point.Measure, Measure)
		"""

	@abc.abstractproperty
	def start(self):
		"""
		Points *must* return the instance, &self:

		[ Invariants ]
		#!/pl/python
			assert point.start is point
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		The next Point according to the unit:

		[ Invariants ]
		#!/pl/python
			assert point.stop == point.elapse(point.Measure(1))
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The magnitude of the Point. For Points, this *must* be one::

		#!/pl/python
			assert pit.magnitude == 1
		"""

	@abc.abstractmethod
	def measure(self, pit):
		"""
		Return the measurement, &Measure instance, between &self and
		the given point in time, &pit. The delta between the two points.
		"""

	@abc.abstractmethod
	def elapse(self, *units, **parts):
		"""
		Returns an adjusted measure in time by the given arguments and keywords.

		Essentially, this is a call to the &of
		method with the instance as the first parameter.

		This is shorthand for `T.of(T, *units, **parts)`.
		"""

	@abc.abstractmethod
	def rollback(self, *units, **parts):
		"""
		The point in time that occurred the given number of units before this
		point. The semantics are identical to &Point.elapse, but transforms
		the parameters into negative values.

		[ Invariants ]

		#!/pl/python
			pit == (pit.rollback(*measures, **units)).elapse(*measures, **units)
		"""

	@abc.abstractmethod
	def leads(self, pit):
		"""
		Returns whether or not the Point in Time, self,
		comes *before* the given argument, &pit.

		Essentially, this is a &Unit aware comparison.
		"""

	@abc.abstractmethod
	def follows(self, pit):
		"""
		Returns whether or not the Point in Time, self,
		comes *after* the given argument, &pit.
		"""

class Clock(metaclass=abc.ABCMeta):
	"""
	"Clock instances" are a collection of clock based tools.
	"""

	@abc.abstractproperty
	def unit(self):
		"""
		The precision of the clock and its methods.

		Hopefully, nanoseconds or microseconds.
		"""

	@abc.abstractmethod
	def sleep(self, quantity):
		"""
		Sleep, block the processing of code according to the given measure of
		time.
		"""

	@abc.abstractmethod
	def meter(self):
		"""
		Returns an iterator to the total measure of time that has elapsed since
		the first iteration of the returned object.

		If it is the first iteration, zero *must* be returned.
		"""

	@abc.abstractmethod
	def delta(self):
		"""
		Construct a new iterator to the measure of time that has elapsed since
		the previous iteration of the returned object. If it is the first
		iteration, zero *must* be returned.
		"""

	@abc.abstractmethod
	def periods(self, quantity):
		"""
		Construct a new iterator yielding a pair, (count, remainder).
		Where the `count` is the number of times that the period has passed
		since the last iteration and the `remainder` is the amount of time
		until another has elapsed.

		Period iterators are primarily used to poll for chunks of elapsed
		time. Whereas, &delta iterators only offer the finest
		grain available.
		"""

	@abc.abstractmethod
	def stopwatch(self):
		"""
		Return a context manager that measures the amount of time that has
		elapsed since the invocation of &__enter__. The yielded
		object is a reference to the elapsed time and can be referenced prior
		to the exit of the context manager.

		Once &__exit__ is called, the elapsed time must no longer
		be measured and the result is subsequently consistent.
		"""

	@abc.abstractmethod
	def monotonic(self):
		"""
		Return a Measure snapshot of the monotonic timer associated with the clock instance.
		"""

	@abc.abstractmethod
	def demotic(self):
		"""
		Return a snapshot of the clock in wall clock time according to the UTC
		timezone.

		In contrast to monotonic.
		"""

	@abc.abstractmethod
	def adjust(self, units):
		"""
		Adjust the demotic clock according to the given number of units.
		"""
