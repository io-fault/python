"""
Abstract base classes for time measures and points.

The inheritance hierarchy can get messy. These ABCs help to keep the inheritance
under control and provide easy access to the APIs.
"""
import abc

class Exception(Exception):
	pass

class TransformationError(Exception):
	"""
	An attempt to transform units failed.
	"""
	unit_input = None
	unit_output = None
	context = None

	def __init__(self, *args, context = None, inverse = None):
		self.unit_input, self.unit_output = args
		self.context = context
		self.inverse = inverse

class Inconceivable(TransformationError):
	"""
	An attempt to represent a unit in like-terms was not possible
	given the current implementation.

	Usually raised when a finite term attempts to convert an indefinite term or an
	ambiguous term.
	"""

class FormatError(Exception):
	pass

class ParseError(FormatError):
	"""
	The exception raised when the format of the datetime could not be parsed.
	"""
	def __init__(self, source, format = None):
		self.format = format
		self.source = source

	def __str__(self):
		return "[{0}] {1}".format(self.format, self.source)

class StructureError(FormatError):
	"""
	The exception raised when the structure of a parsed format could not be
	transformed.
	"""
	def __init__(self, source, struct, format = None):
		self.format = format
		self.struct = struct
		self.source = source

	def __str__(self):
		return "[{0}] ".format(self.format) + self.source + \
			"\n-> " + str(self.struct)

class IntegrityError(FormatError):
	"""
	The exception raised when a parsed point in time is not consistent.

	Notably, in the RFC format, there are portions specifying intersecting
	parts of a timestamp. (The day of week field is arguably superfluous.)
	"""
	def __init__(self, source, struct, tuple, format = None):
		self.format = format
		self.tuple = tuple
		self.struct = struct
		self.source = source

	def __str__(self):
		return "[{0}] ".format(self.format) + self.source + \
			"\n-> " + str(self.struct) + \
			"\n-> " + str(self.tuple) + "\n-> " + str(self.pit)

class Time(metaclass=abc.ABCMeta):
	"""
	The abstract base class for *all* Time related types.
	"""

class Range(Time):
	"""
	The representation of the span between two quantities.

	Often, time quantities are treated as ranges, so rhythm
	makes all time types ranges for practical purposes.
	"""

	@abc.abstractproperty
	def start(self):
		"""
		The beginning of the range.
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		The end of the range. Normally, `stop` is treated in a non-inclusive manner.
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The size of the Range in terms of the :py:attr:`start`.
		"""

	@abc.abstractmethod
	def __contains__(self, pit):
		"""
		Determines whether or not the given `pit` is completely contained by the
		Range.

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
		:py:attr:`.rhythm.abstract.Time.unit`, but potentially different in cases
		where the proper name is not an identifier.
		"""

	@abc.abstractproperty
	def start(self):
		"""
		For Measure instances, this property *must* be zero.

			assert measure.start == 0
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		For Measure instances, this property *must* be the instance, :py:obj:`self`::

			assert measure.stop is measure
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The magnitude of the Time instance. For Measures, this is their integer value::

			assert int(measure) == measure.magnitude
		"""

	@abc.abstractclassmethod
	def of(type, *times, **parts):
		"""
		:param times: A sequence of time instances.
		:type times: :py:class:`.rhythm.abstract.Time`
		:param parts: Keyword names designate the unit of the corresponding value. The time context dictates what that is.
		:type parts: :py:class:`int`

		Create an instance of the type from the sum of the quantities
		specified by `units` and `parts`::

			measure = rhythm.lib.Measure.of(hour = 33, microsecond = 44)
		"""

	@abc.abstractmethod
	def increase(self, *units, **parts):
		"""
		:param units: Variable number of :py:class:`Measure` instances.
		:param parts: Variable keywords whose keys designate the unit.

		Increase the measurement, repositioning the :py:attr:`stop`.

		Returns a new Measure instance whose value is `self` increased by
		the given parameters.

		This is equivalent to::

			assert self.increase(*units, **parts) == self.of(self, *units, **parts)
		"""

	@abc.abstractmethod
	def decrease(self, *units, **parts):
		"""
		:param units: Variable number of :py:class:`Measure` instances.
		:param parts: Variable keywords whose keys designate the unit.

		Decrease the measurement, repositioning the :py:attr:`stop`.

		Returns a new Measure instance whose value is `self` decreased by
		the given parameters.

		This is equivalent to::

			neg_units = [-unit for unit in units]
			neg_parts = {k:-v for (k,v) in parts}

			assert self.decrease(*units, **parts) == self.of(self, *neg_units, **neg_parts)
		"""

	@abc.abstractmethod
	def select(self, part, of = None, align = 0):
		"""
		:param part: The unit whose count is to be returned.
		:type part: :py:class:`str`
		:param of: The unit whose total wholes are subtracted from `self` in order to find the correct total parts.
		:type of: :py:class:`str`
		:param align: How to align the given part. Trivially, this is a difference that is applied prior to removing wholes: `value = self - align`.
		:type align: :py:class:`int`

		Extract the number of complete parts designated by `part` after the last
		complete whole, `of`, with respect to the alignment, `align`.

		The result is a Python :py:class:`int` or an arbitrary object given that
		a Container part is referenced.

		Common cases::

			h = x.select('hour', 'day')
			m = x.select('minute', 'hour')
			s = x.select('second', 'minute')
			u = x.select('microsecond', 'second')
		"""

	@abc.abstractmethod
	def update(self, part, replacement, of = None, align = 0):
		"""
		:param part: The name of the Part unit to set.
		:type part: :py:class:`str`
		:param replacement: The new value to set.
		:type replacement: :py:class:`int`
		:param of: The name of the Whole unit that defines the boundary of the part.
		:type of: :py:class:`str`
		:param align: Defaults to zero; the adjustment applied to the boundary.
		:type align: :py:class:`int`
		:returns: The adjusted time instance.
		:rtype: :py:class:`Time`

		Construct and return a new instance adjusted by the difference between the
		selected part and the given value with respect to the specified alignment.

		The following holds true::

			updated = pit.update(part, replacement, of, align)
			adjusted = this.adjust(**{part: replacement - pit.select(part, of, align)})
			assert updated == adjusted

		It's existence as an interface is due to its utility.
		"""

	@abc.abstractmethod
	def truncate(self, unit):
		"""
		:param unit: The minimum unit size to allow in the new time instance.
		:type unit: :py:class:`str`
		:returns: The adjust time instance.
		:rtype: :py:class:`Time`

		Truncates the time instance to the specified boundary: remove units smaller than the
		specified `unit`.
		"""

class Point(Range):
	"""
	A Point in Time, PiT; a Measure relative to an understood datum.

	Points are an extension of Measures.

	They isolate a position in time *with* a magnitude of one unit.

	The use of magnitudes on Points is purely practical as leveraging this
	with Earth-Day units is far to useful to dismiss.
	"""

	@abc.abstractproperty
	def kind(self):
		"""
		Classification for the unit type with respect to Points in Time.
		"""

	@abc.abstractproperty
	def Measure(self):
		"""
		The Point's corresponding scalar class used to measure deltas. This may
		*not* be the Point's direct superclass, but the following must hold true::

			assert isinstance(point, point.Measure)
		"""

	@abc.abstractproperty
	def start(self):
		"""
		Points *must* return the instance; :py:obj:`self`::

			assert pit.start is pit
		"""

	@abc.abstractproperty
	def stop(self):
		"""
		The next Point according to the unit::

			assert point.stop == point.elapse(point.Measure(1))
		"""

	@abc.abstractproperty
	def magnitude(self):
		"""
		The magnitude of the Point. For Points, this *must* be one::

			assert pit.magnitude == 1
		"""

	@abc.abstractmethod
	def measure(self, pit):
		"""
		Return the measurement, :py:attr:`Measure` instance, between `self` and
		the given point in time. The delta between the two points.
		"""

	@abc.abstractmethod
	def elapse(self, *units, **parts):
		"""
		Returns an adjusted measure in time by the given arguments and keywords.

		Essentially, this is a call to the :py:meth:`.rhythm.abstract.Measure.of`
		method with the instance as the first parameter.

		This is shorthand for ``T.of(T, *units, **parts)``.
		"""

	@abc.abstractmethod
	def rollback(self, *units, **parts):
		"""
		The point in time that occurred the given number of units before this
		point. The functionality is like :py:meth:`Scalar.adjust`, but negates
		the parameters.

		The method's implementation must hold the following properties::

			pit == (pit.ago(*measures, **units)).elapse(*measures, **units)

		Where :py:obj:`pit` is an arbitrary :py:class:`Point`, :py:obj:`measures`
		is a sequence of *compatible* :py:class:`Scalar` instances, and
		:py:obj:`units` is a mapping of unit names to values.
		"""

	@abc.abstractmethod
	def precedes(self, pit):
		"""
		Returns whether or not the Point in Time, self, comes *before* the given argument, `pit`.
		"""

	@abc.abstractmethod
	def proceeds(self, *units, **parts):
		"""
		Returns whether or not the Point in Time, self, comes *after* the given argument, `pit`.
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
		time. Whereas, :py:meth:`delta` iterators only offer the finest
		grain available.
		"""

	@abc.abstractmethod
	def stopwatch(self):
		"""
		Return a context manager that measures the amount of time that has
		elapsed since the invocation of :py:meth:`__enter__`. The yielded
		object is a reference to the elapsed time and can be referenced prior
		to the exit of the context manager.

		Once :py:meth:`__exit__` is called, the elapsed time must no longer
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
