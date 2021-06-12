"""
# Eternals are measures of indefinite units of time. They are used to represent concepts of
# now, never, and the furthest point in time in the past--genesis.
"""
unit = 'eternal'

# Sorted by index use: -1 is always, 0 is whenever, and 1 is never.
points = (
	'whenever', # Any point in time.
	'never',
	'always',
)

# Sorted by index use: -1 is negative, 0 is zero, and 1 is positive.
measures = (
	'zero',
	'positive',
	'negative',
)

def days_from_current_factory(clock, ICE):
	ref = clock.demotic()
	ratio = ref.context.compose(ref.unit, 'day')
	datum = ref.datum * ratio

	def days_from_eternal(eternal, clock = clock, ICE = ICE, ratio = ratio, datum = datum):
		if eternal == 0:
			r = (ratio * int(clock.demotic())) + datum
			return r
		raise ICE('eternal', 'day', inverse = True)
	return days_from_eternal

def eternal_from_days(days):
	"""
	# Definite points in time are considered zero in the indefinite continuum.
	"""
	return 0

def context(ctx, qname = ''):
	measure_instances = None
	point_instances = None
	from . import core

	# eternal units are indifferent to the datum.
	ctx.declare('eternal', 0, kind = 'indefinite')

	class Eternals(core.Measure):
		__slots__ = ()
		unit = unit
		kind = 'indefinite'
		magnitude = 0
		datum = 0
		context = ctx

		name = 'Eternals'
		__name__ = '.'.join((qname, name))
		liketerm = 'eternal'

		def __new__(Class, val):
			# Reduce superfluous quantities.
			if val > 0:
				return measure_instances[1]
			elif val < 0:
				return measure_instances[-1]
			else:
				return measure_instances[0]

		def __float__(self, choice = (0, float('inf'), float('-inf'),)):
			return choice[+self]

		def __neg__(self):
			return measure_instances[-1 * self]

		def __repr__(self, choice = measures):
			return '{0}.{1}'.format(self.__name__, choice[+self])

		def __str__(self, choice = measures):
			return choice[+self]

	measure_instances = tuple(core.Measure.__new__(Eternals, x) for x in (0, 1, -1))

	class Indefinite(core.Point):
		__slots__ = ()
		unit = unit
		kind = 'indefinite'
		magnitude = 0
		datum = Eternals(0) # whenever
		context = ctx

		Measure = Eternals

		name = 'Indefinite'
		__name__ = '.'.join((qname, name))
		liketerm = 'eternal'

		def __new__(Class, val):
			return point_instances[val] # -1 0 +1

		def __neg__(self):
			return point_instances[-1 * self]

		def __float__(self, choice = (0, float('inf'), float('-inf'),)):
			return choice[int(self)]

		def __repr__(self, choice = points):
			return '{0}.{1}'.format(self.__name__, choice[int(self)])

		def __str__(self, strings = points):
			i = int(self)
			return strings[i and i // (abs(i))]

		def leads(self, pit, inversed = None):
			if isinstance(pit, Indefinite):
				assert pit in (0, 1, -1)
				return self < pit
			elif self == 0:
				return pit.of(self).precedes(pit)
			else:
				assert self in (0, 1, -1)
				return (
					None, # whenever
					False, # never
					True, # always
				)[self]
		precedes = leads

		def follows(self, pit, inversed = None):
			if isinstance(pit, Indefinite):
				assert pit in (0, 1, -1)
				return self > pit
			elif self == 0:
				return pit.of(self).follows(pit)
			else:
				assert self in (0, 1, -1)
				return (
					None, # whenever
					True, # never
					False, # always
				)[self]
		proceeds = follows

	point_instances = tuple(core.Point.__new__(Indefinite, x) for x in (0, 1, -1))

	ctx.register_measure_class(Eternals, default = True)
	ctx.register_point_class(Indefinite, default = True)

	ctx.bridge('day', 'eternal', eternal_from_days)
