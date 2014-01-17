"""
Eternals are measures of indefinite units of time. They are used to represent concepts of
now, never, and the furthest point in time in the past--genesis.

Properties::

	Measure.of(eternal = 1) == Measure.of(eternal = (x > 0))
	Measure.of(eternal =-1) == Measure.of(eternal = (x < 0))
	Measure.of(eternal = 0) == Measure.of(eternal = (x = 0))
"""
unit = 'eternal'

#: Sorted by index use: -1 is genesis (past), 0 is now (present), and 1 is never (future).
points = (
	'now',
	'never',
	'genesis',
)
measures = (
	'zero',
	'eternity',
	'ineternity'
)

def eternal_from_days(days):
	"""
	Definite points in time are considered zero in the indefinite continuum.
	"""
	return 0

def context(ctx, qname = ''):
	from . import libunit

	# eternal units are indifferent to the datum.
	ctx.declare('eternal', 0)

	class Eternals(libunit.Measure):
		__slots__ = ()
		unit = unit
		magnitude = 0
		datum = 0
		context = ctx

		name = 'Eternals'
		__name__ = '.'.join((qname, name))
		liketerm = 'eternal'

		@classmethod
		def _init(cls, identifiers = (0, 1, -1)):
			# unorderable is a hack to keep tuple comparisons away
			cls.__cache = tuple(libunit.Measure.__new__(cls, x) for x in identifiers)

		def __new__(cls, val):
			return cls.__cache[val]

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

	class Indefinite(libunit.Point):
		__slots__ = ()
		unit = unit
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
			cls.__cache = tuple(libunit.Point.__new__(cls, x) for x in identifiers)

		def __new__(cls, val):
			return cls.__cache[val]

		def __float__(self, choice = (0, float('inf'), float('-inf'),)):
			return choice[int(self)]

		def __repr__(self, choice = points):
			return '{0}.{1}'.format(self.__name__, choice[int(self)])

		def __str__(self, strings = points):
			i = int(self)
			return strings[i and i // (abs(i))]

		def precedes(self, pit, inversed = None):
			if isinstance(pit, Indefinite):
				assert pit in (0, 1, -1)
				return self < pit
			else:
				assert self in (0, 1, -1)
				return (
					None, # now
					False, # never
					True, # genesis
				)[self]

		def proceeds(self, pit, inversed = None):
			if isinstance(pit, Indefinite):
				assert pit in (0, 1, -1)
				return self > pit
			else:
				assert self in (0, 1, -1)
				return (
					None, # now
					True, # never
					False, # genesis
				)[self]
	Indefinite._init()

	ctx.register_measure_class(Eternals, default = True)
	ctx.register_point_class(Indefinite, default = True)

	ctx.bridge('day', 'eternal', eternal_from_days)
