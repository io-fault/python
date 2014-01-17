"""
System clock management and query interface.
"""
import contextlib
from . import abstract
from . import kernel

class KClock(object):
	"""
	Operating System's :py:class:`rhythm.abstract.Clock` implementation.

	This Class provides access to the kernel's clockwork. It is a thin wrapper providing
	the :py:class:`.abstract.Clock` interface. By default, a process wide instance is
	provided at :py:obj:`.lib.iclock`. That instance should normally be used.
	"""
	__slots__ = ('_monotonic',)
	unit = 'nanosecond'
	clockwork = kernel

	#: Type used to represent measures.
	Measure = int

	#: Type used to represent points.
	Point = int

	def __init__(self):
		# Used as the process' monotonic clock.
		# Forks *must* inherit the state.
		self._monotonic = self.clockwork.Chronometer()

	def monotonic(self):
		return self._monotonic.snapshot()

	def demotic(self):
		return self.clockwork.snapshot_ns()

	def sleep(self, x):
		return self.clockwork.sleep_ns(x)

	def delta(self):
		return self.clockwork.Chronometer()

	def meter(self, delay = 0):
		meter = self.delta()
		# yield zero and init the chronometer's previous value
		yield next(meter)
		# from here, we just grab snapshots and let the device do the math
		get = meter.snapshot
		del meter
		if delay:
			while True:
				yield get()
				self.sleep(delay)
		else:
			del delay
			while True:
				yield get()

	def periods(self, period):
		current = 0
		for x in self.delta():
			current += x
			if current > period:
				count, current = divmod(current, period)
				yield (count, period - current)
			else:
				yield (0, period - current)

	@contextlib.contextmanager
	def stopwatch(self, Measure = int):
		meter = self.meter().__next__
		cell = []
		def inspect(meter=meter,cell=cell):
			if cell:
				return cell[0]
			else:
				return Measure(meter())
		try:
			meter() # start it
			yield inspect
		finally:
			cell.append(Measure(meter()))
abstract.Clock.register(KClock)

class IClock(object):
	"""
	Clock class for binding Point and Measure types with the underlying clockwork's data.
	"""
	__slots__ = ('unit', 'clockwork', 'Point', 'Measure')

	def __init__(self, clockwork, Measure, Point):
		self.Point = Point
		self.Measure = Measure
		self.clockwork = clockwork
		self.unit = self.clockwork.unit

	def monotonic(self):
		return self.Measure(self.clockwork.monotonic())

	def demotic(self):
		return self.Point(self.clockwork.demotic())

	def sleep(self, x):
		if isinstance(x, abstract.Measure):
			y = self.Measure.of(x)
			z = y.select('nanosecond')
		else:
			z = x

		return self.Measure(self.clockwork.sleep(z))

	def delta(self, map = map):
		return map(self.Measure, self.clockwork.delta())

	def meter(self, *args, **kw):
		return map(self.Measure, self.clockwork.meter())

	def periods(self, period):
		for count, period in self.clockwork.periods(period.select('nanosecond')):
			yield (count, self.Measure(period))

	def stopwatch(self):
		return self.clockwork.stopwatch(Measure = self.Measure)
abstract.Clock.register(IClock)

#: Primary Kernel Clock
kclock = KClock()
