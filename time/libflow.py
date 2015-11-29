"""
Tools for tracking arbitrary units over a period of time, rates.

The classes and function herein are requisites for time based rate limiting.
"""

import collections
import weakref

# Use the Chronometer directly for performance reasons.
from . import kernel

# But some surface functionality can return Measures for typed units
from . import library

class Radar(object):
	"""
	Radars track the rate of arbitrary flows across units of time.
	By default, objects are tracked using a
	&weakref.WeakKeyDictionary. This allows for casual tracking
	to take place such that explicit disposal is not necessary.

	! WARNING:
		&Radars are not thread safe with respect to particular subjects.
	"""
	__slots__ = ('tracking', 'unit', 'Chronometer', 'Queue')

	def __init__(self,
			Chronometer=kernel.Chronometer,
			Dictionary=weakref.WeakKeyDictionary,
			Queue=collections.deque
		):
		"""
		Create a new Radar instance for tracking a set of flows.
		"""

		self.tracking = Dictionary()
		self.Chronometer = Chronometer
		self.Queue = Queue
		self.unit = 'nanosecond'

	@staticmethod
	def split(seq:collections.Iterable, pit:int, int=int, iter=iter):
		"""
		Split the given sequence, &seq, at the relative point in time, &pit.

		Returns a pair of sequences split at the given &pit.

		[Parameters]
		/seq
			A sequence of `(units, time)` pairs.
		/pit
			A point in time relative to the beginning of the sequence.
		"""

		# if the times weren't relative, we could bisect.
		count = 0
		replacement = None
		prefix = []
		suffix = []
		i = iter(seq)
		for pair in i:
			u, t = pair
			if t > pit:
				# last entry that needs to be processed
				# calculate the average rate according to
				# this frame and truncate it according to the
				# remainder of the pit.
				pv = int((u / t) * pit) # prefix units
				prefix.append((pv, pit))
				# the remainder goes to the suffix
				suffix.append((u - pv, t - pit))
				break
			else:
				# subtract the time from the pit and continue
				pit = pit - t
				prefix.append(pair) # wholly consumed
		for pair in i:
			suffix.append(pair)

		return prefix, suffix

	@staticmethod
	def sums(seq, Measure = library.Measure):
		"""
		Given a sequence of (time, units) pairs,
		return the sums of the columns.
		"""

		total_units, total_time = 0, 0
		for units, time in seq:
			total_units += units
			total_time += time

		return (total_units, Measure(total_time))

	def forget(self, subject):
		"""
		Forget all tracking information about the given object, &subject.

		This removes the subject from the dictionary of tracked objects.

		Returns the value of the forgotten key, &subject.

		! NOTE:
			By default, the dictionary is a WeakKeyDictionary.
			Using &forget is not necessary unless an
			override for the dictionary type was given.

		[Parameters]

		/subject
			The tracked object to be removed.
		"""

		return self.tracking.pop(subject, None)

	def track(self, subject, units):
		"""
		Given an object, track the units.
		"""

		if subject not in self.tracking:
			pair = self.tracking[subject] = (self.Chronometer(), self.Queue())
		else:
			pair = self.tracking[subject]

		d, q = pair
		q.append((units, next(d)))

		return pair

	def reset(self, next=next):
		"""
		During cases where a process is suspended, SIGSTOP and SIGCONT,
		the reset method can be used to ignore the elapsed time for *all*
		tracked objects.

		For individual objects, see &skip.

		Returns &None.
		"""

		for pair in self.tracking.values():
			next(pair[0])

	def skip(self, subject, next=next):
		"""
		Skip the elapsed time for the given subject.

		Returns amount of time skipped as an &int.
		"""

		return next(self.tracking[subject][0])

	def zero(self, subject, Measure = library.Measure, next = next):
		"""
		Zero out the Chronometer for the given subject.

		In cases where consumed time should be skipped for the subsequent track operation,
		this method can be used to cause the consumed time to not be added to the tracked
		time.

		Notably, zero is useful in cases where flow can be paused and unpaused.

		Returns the amount of time dropped as a &.library.Measure instance.

		[Parameters]

		/subject
			The object whose flow-time is to be zeroed.
		"""

		pair = self.tracking.get(subject)

		if pair is not None:
			r = next(pair[0])
		else:
			r = 0

		return Measure(r)

	def collapse(self, subject:object, window:int=0, range=range):
		"""
		Collapse calculates the tracked units and time of a given flow and replaces
		the set of records with a single record containing the totals. If a window
		is given, the consistency of the specified time frame will remain intact,
		but everything that comes before it will be aggregated into a single
		record.

		This offers an alternative to truncate given cases where overall
		data is still needed.

		Returns the number of records collapsed.

		[Parameters]
		/subject
			The object whose flow is to be collapsed.
		/window
			The window of the flow to maintain.
		"""

		# Make sure there is an element within the window.
		d, q = self.track(subject, 0)

		size = len(q)
		# allow concurrent tracks to be performed; use the same chronometer

		popleft = q.popleft
		b, a = self.split(reversed([popleft() for x in range(size)]), window)
		q.extendleft(reversed(b)) # maintain window
		collapsed_to = self.sums(a) # aggregate suffix
		q.appendleft(collapsed_to) # prefix totals

		return collapsed_to

	def truncate(self, subject:object, window:library.Measure):
		"""
		For the given object, truncate the tracked data according to the specified
		window of time units. All record data prior to the window will be
		discarded.

		Returns the number of records removed.

		[Parameters]
		/subject
			The tracked object.
		/window
			The amount of time in the past to retain.
		"""

		# Make sure there is an element within the window and used up-to-date info
		d, q = self.track(subject, 0)

		size = len(q)
		# allow concurrent tracks to be performed; use the same chronometer

		b, a = self.split(reversed([q.popleft() for x in range(size)]), window)
		q.extendleft(reversed(b)) # maintain window
		return a

	def rate(self, subject, window = None):
		"""
		Construct a tuple of the (total units, total time) for
		the given subject and within the specified window.

		If no window is provided, the overall units over time will be returned.

		Uses the &sums method to construct the product.

		[Parameters]
		/subject
			The tracked object.
		/window
			The limit of view of the rate.
		"""

		if subject in self.tracking:
			seq = self.tracking[subject][-1]
			if window is not None:
				# limit the view to the window
				seq = self.split(reversed(seq), window)[0]
			return self.sums(seq)

	def all(self, window, Measure=library.Measure):
		"""
		Scan the entire set of tracked objects updating their rate according to
		a zero-units in order to get an up-to-date snapshot of the rate of all
		tracked objects for the given window.

		! WARNING:
			Given the processing time necessary to calculate the totals
			for all tracked flows, overall may not ever be able to give
			an accurate answer.

		[Parameters]
		/window
			The size of the window to view.
		"""

		keys = list(self.tracking.keys())
		total_u = 0
		total_t = library.Measure(0)
		track = self.track
		split = self.split
		sums = self.sums
		count = 0

		for x in keys:
			count += 1
			u, t = sums(split(reversed(track(x, 0)[1]), window)[0])
			total_u += u
			total_t += t

		# limit the amount to the given window
		return (total_u, (Measure(total_t), count))
