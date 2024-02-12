"""
# Typed system clock access.

# Construct instances of both the real and monotonic clocks and provide access
# via &elapsed, &utc, &local, and &date.
"""
from ..context import tools
from . import constants
from . import types

def _fault_clocks(module, delta):
	return (
		module.Real().adjust(-delta).get,
		module.Monotonic().get,
	)

def _stdlib_clocks(module, delta):
	def _real_clock_read(time=module.time, delta=delta):
		t = time()
		i = t.__int__()
		s = (t - i) * 1000000000
		i -= delta
		return (i + s)

	try:
		mc = module.monotonic_ns
	except:
		# XXX: Needs runtime warning.
		mc = _real_clock_read

	return rc, mc

def setup():
	try:
		from ..system import clocks as source
		clocks = _fault_clocks
	except ImportError:
		# Fallback to stdlib.
		import time as source
		clocks = _stdlib_clocks

	return clocks(source, types.core.unix_epoch_delta)

_real_clock_read, _monotonic_clock_read = setup()
del setup, _fault_clocks, _stdlib_clocks
def _unix(ut, *, epoch=constants.unix_epoch.elapse):
	return epoch(second=ut)

@tools.cachedcalls(16)
def zone(selector=None):
	"""
	# Using the zone definitions provided by the system,
	# construct a view for the time zone identified by &selector.

	# [ Parameters ]
	# /selector/
		# The zone's identifier.
		# If &None, the system default zone will be used.
	"""
	from . import views # Defer import until usage.
	return views.Zone.open(_unix, selector or views.tzif.tzdefault)

def utc(*, Type=types.Timestamp) -> types.Timestamp:
	"""
	# Get the current time according to the system's real clock.
	"""
	return Type(_real_clock_read())

def local(*, Type=types.Timestamp) -> types.Timestamp:
	"""
	# Get the current time according to the system's real clock and
	# the default time zone configured by the system.

	# The applied offset returned by &.views.Zone.localize is discarded by this
	# function, and, therefore, it should only be used in cases where it is
	# acceptable for the timestamp to be represented without a time zone.

	# The default zone can be changed by overriding the &zone function.
	"""
	return zone().localize(Type(_real_clock_read()))[0]

def date(delta=0, *, Type=types.Date) -> types.Date:
	"""
	# Using &local, identify the current date.

	# [ Parameters ]
	# /delta/
		# The day offset to apply to the current date.
		# Defaults to zero.
	"""
	return Type.of(local()).elapse(day=delta)

def elapsed(*, Type=types.Measure) -> types.Measure:
	"""
	# Snapshot of the system's monotonic clock.
	"""
	return Type(_monotonic_clock_read())
