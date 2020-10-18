"""
# Various constants.

# [ Properties ]

# /never/
	# The latest Point in time. Positive infinity.
# /present/
	# The midpoint point of &genesis and &never.
	# Intended for symbolic references the current time.
# /genesis/
	# The earliest Point in time. Negative infinity.
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

# Furthest Point in the future.
never = types.Indefinite(1)

# Furthest Point in the past.
genesis = types.Indefinite(-1)

# Current Point in Time, always moving.
present = types.Indefinite(0)

# Segment representing all time. All points in time exist in this segment.
continuum = types.Segment((genesis, never))
