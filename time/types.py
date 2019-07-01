"""
# Common time domains.

# Aside from &Segment, all types in this module are subclasses of &builtins.int.
"""
from . import core

# Range class.
Segment = core.Segment

Context, MeasureTypes, PointTypes = core.standard_context(__name__)

# A tuple containing all of the default Scalar types.
MeasureTypes = MeasureTypes

# Scalar with finest, default, representation type precision.
# Currently this is nanosecond precision.
Measure = MeasureTypes[0]

# Scalar in earth-days.
Days = MeasureTypes[1]

# Scalar in seven earth-days.
Weeks = MeasureTypes[2]

# Scalar in Gregorian Months.
Months = MeasureTypes[3]

# A tuple containing all of the default Point in Time types.
PointTypes = PointTypes

# Point In Time with Measure's precision.
Timestamp = PointTypes[0]

# Point In Time with earth-day precision.
Date = PointTypes[1]

# Point In Time with seven earth-day precision.
Week = PointTypes[2]

# Point In Time with Gregorian Month precision.
GregorianMonth = PointTypes[3]

# Infinite measure unit.
Eternals = Context.measures['eternal'][None]

# Infinite unit points. Class used for genesis, never, and now.
Indefinite = Context.points['eternal'][None]

def from_unix_timestamp(unix_timestamp, Timestamp = Timestamp.of):
	"""
	# Create a &Timestamp instance *from seconds since the unix epoch*.

	#!/pl/python
		assert types.from_unix_timestamp(0) == types.Timestamp.of(iso='1970-01-01T00:00:00.0')

	# For precision beyond seconds, a subsequent elapse can be used.

	#!/pl/python
		float_ts = time.time()
		nsecs = int(float_ts)
		us = int((float_ts - nsecs) * 1000000)
		x = types.from_unix_timestamp(nsecs)
		x = x.elapse(microsecond=us)
	"""
	return Timestamp(unix=unix_timestamp)
