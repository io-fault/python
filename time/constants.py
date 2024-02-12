"""
# Various constants.

# [ Elements ]

# /never/
	# Point at positive infinity.
# /always/
	# Point at negative infinity.
# /whenever/
	# Any point in time.
# /zero/
	# Precision indifferent zero measurement.
# /eternity/
	# Positive infinity measurement.
# /unix_epoch/
	# &types.Timestamp instance referring to 1970.
# /local_datum/
	# &types.Timestamp instance refrerring to the datum used by the project.
"""
from . import types

annum = types.Measure.of(second=(86400*365)+(86400//4)) # Julian Year, 525960 minutes.
unix_epoch = types.Timestamp.of(year=1970)
local_datum = types.Timestamp(0)

if True:
	Eternals = types.Context.measures['eternal'][None]
	Indefinite = types.Context.points['eternal'][None]

	zero = Eternals(0)
	infinity = Eternals(1)
	never = Indefinite(1)
	always = Indefinite(-1)
	whenever = Indefinite(0)

	del Eternals, Indefinite
