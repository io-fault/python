"""
# Various &types constants.

# [ Properties ]

# /genesis/
	# The earliest Point in time. Negative infinity.
# /never/
	# The latest Point in time. Positive infinity.
# /present/
	# The point between &genesis and &never.
# /continuum/
	# A segment whose start is &genesis and end is &never.
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
