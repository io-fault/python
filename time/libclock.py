"""
System clock management and query interface.
"""
import contextlib
import functools
from . import abstract
from . import system as clockwork

class Clock(object):
	"""
	Operating System's :py:class:`rhythm.abstract.Clock` implementation.
	"""
	__slots__ = ('unit', 'lib', 'clockwork', '_monotonic', '_sleeper')

	def __init__(self, unit, lib, clockwork = clockwork):
		self.unit = unit
		self.lib = lib
		self.clockwork = clockwork
		# Used as the process' monotonic clock.
		# Forks *must* inherit the state.
		self._monotonic = self.clockwork.Chronometer()
		class Sleeper(clockwork.Sleeper):
			__slots__ = ()
			def __next__(self, Measure = lib.Measure):
				return Measure(super().__next__())
		self._sleeper = Sleeper

	def sleep(self, x):
		return self.lib.Measure(self.clockwork.sleep_ns(x))

	def sleeper(self):
		return self._sleeper()

	def delta(self, _map=map):
		return _map(self.lib.Measure, self.clockwork.Chronometer())

	def meter(self, *args, **kw):
		m = self.lib.Measure
		delay = m.of(*args, **kw)
		meter = self.clockwork.Chronometer()
		del args
		del kw
		# yield zero and init the chronometer's previous value
		yield m(next(meter))
		# from here, we just grab snapshots and let the device do the math
		get = meter.snapshot
		del meter
		if delay:
			while True:
				yield m(get())
				self.sleep(delay)
		else:
			del delay
			while True:
				yield m(get())

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
	def stopwatch(self, _partial = functools.partial):
		meter = self.meter().__next__
		cell = []
		def inspect(meter=meter,cell=cell):
			if cell:
				return cell[0]
			else:
				return meter()
		try:
			meter() # start it
			yield inspect
		finally:
			cell.append(meter())

	def monotonic(self):
		return self.lib.Measure(self._monotonic.snapshot())

	def demotic(self):
		return self.lib.Timestamp(self.clockwork.snapshot_ns())
abstract.Clock.register(Clock)
