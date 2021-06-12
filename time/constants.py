"""
# Various constants.

# [ Properties ]

# /zero/
	# Precision indifferent zero measurement.
# /eternity/
	# Positive infinity measurement.
# /never/
	# Point at positive infinity.
# /whenever/
	# Any point in time.
# /always/
	# Point at negative infinity.
# /continuum/
	# A segment whose start is &genesis and end is &never.
# /unix_epoch/
	# &types.Timestamp instance referring to 1970.
# /local_datum/
	# &types.Timestamp instance refrerring to the datum used by the project.
"""
from . import types

annum = types.Measure.of(second=(86400*365)+(86400//4)) # Julian Year
unix_epoch = types.from_unix_timestamp(0)
local_datum = types.Timestamp(0)

# Precision independent zero.
zero = types.Eternals(0)

# Positive infinity measure.
eternity = types.Eternals(1)

# Furthest Point in the future.
never = types.Indefinite(1)

# Furthest Point in the past.
always = types.Indefinite(-1)

# Any Point in time.
whenever = types.Indefinite(0)

# Segment representing all time. All points in time exist in this segment.
continuum = types.Segment((always, never))
