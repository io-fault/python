"""
# Typed System Clock access.
"""
from . import types

try:
	from ..system import clocks

	_real_clock_read = clocks.Real().adjust(-types.core.unix_epoch_delta).get
	_monotonic_clock_read = clocks.Monotonic().get

	del clocks
except ImportError:
	import time

	def _real_clock_read(time=time.time, delta=types.core.unix_epoch_delta):
		t = time()
		i = t.__int__()
		s = (t - i) * 1000000000
		i -= delta
		return (i + s)

	try:
		_monotonic_clock_read = time.monotonic_ns
	except:
		# XXX: Needs runtime warning.
		_monotonic_clock_read = _real_clock_read

	del time

def now(Timestamp=types.Timestamp) -> types.Timestamp:
	"""
	# Get the current point in time according to the system's real clock as a &types.Timestamp.
	"""
	return Timestamp(_real_clock_read())

def elapsed(Measure=types.Measure) -> types.Measure:
	"""
	# Snapshot of the system's monotonic clock. Returns a &types.Measure.
	"""
	return Measure(_monotonic_clock_read())
