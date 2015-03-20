"""
libflow provides tools for tracking arbitrary units over a period of time.

The classes and function herein are requisites for time based rate limiting.
"""
import collections
import weakref
# Use the Chronometer directly for performance reasons.
from . import kernel
# But some surface functionality can return Measures for typed units
from . import lib

class Radar(object):
	"""
	Radars track the rate of arbitrary flows across units of time.
	By default, objects are tracked using a
	:py:class:`weakref.WeakKeyDictionary`. This allows for casual tracking
	to take place such that explicit disposal is not necessary.
	However, it is possible to use a regular dictionary by providing a type via
	the ``Dictionary`` keyword argument.

	**Radars are not thread safe with respect to particular subjects.**
	"""
	__slots__ = ('tracking', 'unit', 'Chronometer', 'Queue')

	@staticmethod
	def split(seq, pit, int = int, iter = iter):
		"""
		split(seq, pit)

		:param seq: A sequence of `(units, time)` pairs.
		:type seq: :py:class:`collections.Iterable`
		:param pit: A point in time relative to the beginning of the sequence.
		:type seq: :py:class:`int`
		:returns: A pair of sequences split at the given `pit`.
		:rtype: :py:class:`list`

		Split the given sequence at the relative point in time within the given
		sequence, `seq`.
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
	def sums(seq, Measure = lib.Measure):
		"""
		sums(seq)

		Given a sequence of (time, units) pairs,
		return the sums of the columns.
		"""
		total_units, total_time = 0, 0
		for units, time in seq:
			total_units += units
			total_time += time
		return (total_units, Measure(total_time))

	def __init__(self,
		Chronometer = kernel.Chronometer,
		Dictionary = weakref.WeakKeyDictionary,
		Queue = collections.deque
	):
		"""
		Radar()

		Create a new Radar instance for tracking a set of flows.
		"""
		self.tracking = Dictionary()
		self.Chronometer = Chronometer
		self.Queue = Queue
		self.unit = 'nanosecond'

	def __len__(self):
		"""
		Return the number of flows being tracked.
		"""
		return len(self.tracking)

	def forget(self, subject):
		"""
		:param subject: The tracked object to be removed.
		:type subject: :py:class:`object`
		:returns: The value of the forgotten key, `subject`.
		:rtype: :py:class:`object`

		Forget all tracking information about the given object, `subject`.

		This removes the subject from the dictionary of tracked objects.

		.. note::	By default, the dictionary is a WeakKeyDictionary.
						Using `forget` is not necessary unless an
						override for the dictionary type was given.
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

	def reset(self, next = next):
		"""
		reset()

		:returns: :py:obj:`None`

		During cases where a process is suspended, SIGSTOP and SIGCONT, the reset method can
		be used to ignore the elapsed time for *all* tracked objects.

		For individual objects, see :py:meth:`skip`.
		"""
		for pair in self.tracking.values():
			next(pair[0])

	def skip(self, subject, next = next):
		"""
		skip(subject)

		:returns: Amount of time skipped.
		:rtype: :py:class:`int`

		Skip the elapsed time for the given subject.
		"""
		return next(self.tracking[subject][0])

	def zero(self, subject, Measure = lib.Measure, next = next):
		"""
		zero(subject)

		:param subject: The object whose flow-time is to be zeroed.
		:type subject: :py:class:`object`
		:returns: The amount of time dropped.
		:rtype: :py:class:`.lib.Measure`

		Zero out the Chronometer for the given subject.

		In cases where consumed time should be skipped for the subsequent track operation,
		this method can be used to cause the consumed time to not be added to the tracked
		time.

		Notably, zero is useful in cases where flow can be paused and unpaused.
		"""
		pair = self.tracking.get(subject)
		if pair is not None:
			r = next(pair[0])
		else:
			r = 0
		return Measure(r)

	def collapse(self, subject, window = 0, range = range):
		"""
		collapse(subject, window = 0)

		:param subject: The object whose flow is to be collapsed.
		:type subject: :py:class:`object`
		:param window: The window of the flow to maintain.
		:type window: :py:class:`int`
		:returns: The number of records collapsed.
		:rtype: :py:class:`int`

		Collapse calculates the tracked units and time of a given flow and replaces
		the set of records with a single record containing the totals. If a window
		is given, the consistency of the specified time frame will remain intact,
		but everything that comes before it will be aggregated into a single
		record.

		This offers an alternative to truncate given cases where overall
		data is still needed.
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

	def truncate(self, subject, window):
		"""
		:param subject: The tracked object.
		:type subject: :py:class:`object`
		:param window: The amount of time in the past to retain.
		:type window: :py:class:`.lib.Measure`
		:returns: The number of records removed.
		:rtype: :py:class:`int`

		For the given object, truncate the tracked data according to the specified
		window of time units. All record data prior to the window will be
		discarded.
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
		:param subject: The tracked object.
		:type subject: :py:class:`object`
		:param window: The limit of view of the rate.
		:type window: :py:class:`int` | :py:class:`NoneType`

		Construct a tuple of the (total units, total time) for
		the given subject and within the specified window.

		If no window is provided, the overall units over time will be returned.

		Uses the :py:meth:`sums` method to construct the product.
		"""
		if subject in self.tracking:
			seq = self.tracking[subject][-1]
			if window is not None:
				# limit the view to the window
				seq = self.split(reversed(seq), window)[0]
			return self.sums(seq)

	def all(self, window, Measure = lib.Measure):
		"""
		all(window)

		Scan the entire set of tracked objects updating their rate according to
		a zero-units in order to get an up-to-date snapshot of the rate of all
		tracked objects for the given window.

		.. warning:: Given the processing time necessary to calculate the totals
		             for all tracked flows, overall may not ever be able to give
		             an accurate answer.
		"""
		keys = list(self.tracking.keys())
		total_u = 0
		total_t = lib.Measure(0)
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
