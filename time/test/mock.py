"""
# Test support classes
"""

class Chronometer(object):
	'Mock chronometer'
	value = 0

	@classmethod
	def set(typ, elapsed):
		typ.value = elapsed

	def __next__(self):
		x = self.value
		self.set(0)
		return x

