"""
Coordinate the occurrence of events.
"""
import itertools
import collections
import heapq

class Harmony(object):
	"""
	All purpose event scheduler.

	Coorindate the production of events according to a time delay against a monotonic timer.

	Each Defers instance manages the production of a set of events according to the
	prescribed delay. When an event is scheduled, the amount of time specified is added to the
	meter's current position. When the meter surpasses that value, the event is emitted.

	Events are arbitrary Python objects. Often, they will be tasks to be performed.

	Harmony differs from Python's scheduler as there is no attempt to manage the sleep
	period. Rather, this responsibility is offloaded onto the user in order to keep
	functionality isolated.
	"""
	unit = 'nanosecond'

	from .kernel import Chronometer

	def __init__(self,
		Chronometer = Chronometer,
		Identifiers = itertools.count,
		DefaultDict = collections.defaultdict,
		Sequence = collections.deque
	):
		self.meter = Chronometer()
		self.heap = []
		# RPiT to (Eventi) Id's Mapping
		self.schedule = DefaultDict(Sequence)
		self.cancellations = set()

	def period(self):
		"""
		The period before the next event should occur.

		When combining Harmony instances, this method can be used to identify
		when this Harmony instance should be processed.
		"""
		try:
			smallest = self.heap[0]
			return smallest.__class__(smallest - self.meter.snapshot())
		except IndexError:
			return None

	def cancel(self, *events):
		"""
		Cancel the scheduled events.
		"""
		# Update the set of cancellations immediately.
		# This set is used as a filter by Defer cycles.
		self.cancellations.update(events)

	def put(self, *schedules, push = heapq.heappush):
		"""
		put(*schedules)

		:param schedules: The Measure, Event pairs.
		:type schedules: (:py:class:`.lib.Measure`, :py:class:`object`)
		:returns: A sequence of event identifiers that can be used for cancellation.
		:rtype: [:py:class:`int`]

		Schedules the given events for execution.
		"""
		snapshot = self.meter.snapshot()
		events = []
		try:
			curmin = self.heap[0]
		except:
			curmin = None

		for assignment in schedules:
			measure, event = assignment
			pit = measure.__class__(measure + snapshot)

			push(self.heap, pit)
			self.schedule[pit].append(event)

		return events

	def get(self, pop = heapq.heappop, push = heapq.heappush):
		"""
		:rtype: [(:py:class:`.library.Measure`, :py:class:`object`), ...]

		Return all events whose sheduled delay has elapsed according to the Chronometer.

		The pairs within the returned sequence consist of a Measure and the Event. The
		measure is the amount of time that has elapsed since the scheduled time.
		"""
		events = []
		cur = self.meter.snapshot()
		while self.heap:
			# repeat some work in case of concurrent pop
			item = pop(self.heap)
			overflow = item.__class__(cur - item)

			# the set of callbacks have passed their time.
			if overflow < 0:
				# not ready. put it back...
				push(self.heap, item)
				break
			else:
				eventq = self.schedule[item]
				while eventq:
					x = eventq.popleft()
					if x in self.cancellations:
						# filter any cancellations
						# schedule is already popped, so remove event and cancel*
						self.cancellations.discard(x)
					else:
						events.append((overflow, x))
				if not events:
					self.schedule.pop(item, None)
		return events
