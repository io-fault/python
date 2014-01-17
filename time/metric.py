"""
Information about the metric second and its multiples.
"""

#: The names of the SI multiples associated with their exponent.
name_to_exponent = {
	'yoctosecond': -24,
	'zeptosecond': -21,
	'attosecond': -19,
	'femtosecond': -15,
	'picosecond': -12,
	'nanosecond': -9,
	'microsecond': -6,
	'millisecond': -3,
	'centisecond': -2,
	'decisecond': -1,
	'second': 0,
	'decasecond': 1,
	'hectosecond': 2,
	'kilosecond': 3,
	'megasecond': 6,
	'gigasecond': 9,
	'terasecond': 12,
	'petasecond': 15,
	'exasecond': 18,
	'zettasecond': 21,
	'yottasecond': 24,
}

#: A mapping of exponents to SI multiple names.
exponent_to_name = dict([(v,k) for k,v in name_to_exponent.items()])

#: Abbreviations of the SI multiple names.
abbreviations = {
	-1: 'ds',
	-2: 'cs',
	-3: 'ms',
	-6: 'µs',
	-9: 'ns',
	-12: 'ps',
	-15: 'fs',
	-18: 'as',
	-21: 'zs',
	-24: 'ys',
	0: 's',
	1: 'das',
	2: 'hs',
	3: 'ks',
	6: 'Ms',
	9: 'Gs',
	12: 'Ts',
	15: 'Ps',
	18: 'Es',
	21: 'Zs',
	24: 'Ys',
}

def context(context):
	"""
	Given a libunit.Context instance, define the metric units starting with the
	'second'.
	"""
	import fractions
	import operator

	l = list(name_to_exponent.items())
	l.sort(key=operator.itemgetter(1))

	context.define(l[0][0], 'second', l[0][1], fractions.Fraction(10,1))

	for i in range(1, len(l)):
		# define the unit with the prior definition
		defined = l[i]
		definition = l[i-1]

		context.define(
			defined[0], definition[0],
			defined[1] - definition[1],
			fractions.Fraction(10, 1)
		)
