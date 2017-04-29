"""
# Rate specification primitive for managing contraint configuration.
"""

class Specification(tuple):
	"""
	# Structure used to define the throughtput for enforcing rate requirements.

	# Rate constraints define a minimum, maximum, and the duration window that
	# must be maintained in order to justify a violation event.
	"""
	_keys = ("minimum", "maximum", "window")

	def replace(self, **kw):
		"""
		# Create a new Specification from the instance with the given keywords as overrides to
		# the fields.
		"""
		return self.__new__([
			kw.get(x, getattr(self, x)) for x in self._keys
		])

	@property
	def minimum(self):
		"""
		# The minimum rate for the flow.
		"""
		return self[0]

	@property
	def maximum(self):
		"""
		# The maximum rate for the flow.
		"""
		return self[1]

	@property
	def window(self):
		"""
		# The tracking window of time that the constraint should be applied to.
		"""
		return self[2]

	def position(self, rate):
		"""
		# Where the given rate falls within the designated range.
		"""
		if self[0] is not None and rate < self[0]:
			return -1
		if self[1] is not None and rate > self[1]:
			return 1
		return 0

	def recoverable(self, rate, remainder):
		"""
		# Given the the remainder of time in order to recover,
		# calculate whether or not its possible to come back and
		# meet the minimum requirement within the remainder of time.

		# It is never possible given no remainder of time in the window.
		# It is always possible if no maximum is set.
		"""
		if remainder <= 0:
			return False

		if self.maximum is None:
			# always recoverable if there is no maximum and
			# there is time left.
			return True

		max_throughput = remainder * self.maximum
		transferred = rate * (self[2] - remainder)

		possible = max_throughput + transferred

		# possible rate increase is greater than the minimum
		return (possible / self[2]) >= self[0]

	def throttle(self, rate):
		"""
		# Return the delay that should be applied to the flow to bring the rate back under the
		# defined maximum.
		"""
		# if the rate is less than the maximum, no throttling needs to occur
		if self.maximum is None:
			return 0

		x = (rate / self.maximum) - 1
		if x <= 0:
			return 0
		return x
