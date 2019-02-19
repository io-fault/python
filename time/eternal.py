"""
# Eternals are measures of indefinite units of time. They are used to represent concepts of
# now, never, and the furthest point in time in the past--genesis.
"""
unit = 'eternal'

#: Sorted by index use: -1 is genesis (past), 0 is now (present), and 1 is never (future).
points = (
	'now',
	'never',
	'genesis',
)

#: Sorted by index use: -1 is "ineternity", 0 is eternity, and 1 is eternity.
measures = (
	'zero',
	'eternity',
	'ineternity'
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

		@classmethod
		def _init(cls, identifiers = (0, 1, -1)):
			# unorderable is a hack to keep tuple comparisons away
			cls.__cache = tuple(core.Measure.__new__(cls, x) for x in identifiers)

		def __new__(cls, val):
			# Reduce superfluous quantities.
			if val > 0:
				return cls.__cache[1]
			elif val < 0:
				return cls.__cache[-1]
			else:
				return cls.__cache[0]

		def __float__(self, choice = (0, float('inf'), float('-inf'),)):
			return choice[int(self)]

		def __repr__(self, choice = measures):
			return '{0}.{1}'.format(self.__name__, choice[int(self)])

		def __str__(self, choice = measures):
			return choice[int(self)]

		def __eq__(self, ob):
			if ob.unit != self.unit:
				return int(self)== 0 and int(ob) == 0
	Eternals._init()

	class Indefinite(core.Point):
		__slots__ = ()
		unit = unit
		kind = 'indefinite'
		magnitude = 0
		datum = Eternals(0) # now
		context = ctx

		Measure = Eternals

		name = 'Indefinite'
		__name__ = '.'.join((qname, name))
		liketerm = 'eternal'

		@classmethod
		def _init(cls, identifiers = (0, 1, -1)):
			# unorderable is a hack to keep tuple comparisons away
			cls.__cache = tuple(core.Point.__new__(cls, x) for x in identifiers)

		def __new__(cls, val):
			return cls.__cache[val]

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
					None, # now
					False, # never
					True, # genesis
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
					None, # now
					True, # never
					False, # genesis
				)[self]
		proceeds = follows
	Indefinite._init()

	ctx.register_measure_class(Eternals, default = True)
	ctx.register_point_class(Indefinite, default = True)

	ctx.bridge('day', 'eternal', eternal_from_days)
