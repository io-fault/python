"""
Data and regarding Earth-based units of time. (The earth day)
"""
#: Number of seconds contained in a `minute`.
seconds_in_minute = 60

#: Number of minutes contained in an `hour`.
minutes_in_hour = 60

#: Number of hours contained in an earth `day`.
hours_in_day = 24

#: Number of a days in four Julian years. (365.25 days)
days_in_four_annum = 1461

def context(context):
	import fractions
	# Earth-based/metric
	context.define('hour', 'day',
		1, base = fractions.Fraction(1, hours_in_day))
	context.define('minute', 'hour',
		1, base = fractions.Fraction(1, minutes_in_hour))
	context.define('second', 'minute',
		1, base = fractions.Fraction(1, seconds_in_minute))
	context.define('annum', 'day',
		1, base = fractions.Fraction(days_in_four_annum, 4))

	def pack_subsecond(ti, arg = None, Fraction = fractions.Fraction):
		denom = ti.context.convert('second', ti.unit, 1)
		if denom:
			return Fraction(
				ti.select(ti.unit, 'second'),
				denom
			)
		return 0

	def unpack_subsecond(typ, subsecond):
		# the of method will appropriately apply conversion handling fractional
		# seconds and floating point seconds.
		return (('second', subsecond),)
	context.container('subsecond', pack_subsecond, unpack_subsecond)

	# Define container units.
	def unpack_timeofday_tuple(typ, todt):
		return zip(('hour', 'minute', 'second'), todt)
	def pack_timeofday_tuple(pit, arg):
		return (
			pit.select('hour', 'day'),
			pit.select('minute', 'hour'),
			pit.select('second', 'minute'),
		)
	context.container('timeofday', pack_timeofday_tuple, unpack_timeofday_tuple)
