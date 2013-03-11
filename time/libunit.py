"""
Defines the time Context that constructs unit types and manages their
relationship to other unit types.

The contents of this module are largely the mechanics under the hood and should
not be used directly.

.. danger:: NOTHING IN THIS FILE SHOULD BE RELIED UPON.
.. danger:: THESE INTERFACES ARE SUBJECT TO CHANGE WITHOUT WARNING
"""
import collections
import fractions
import functools
import operator
from . import abstract

class Unit(int):
	"""
	The base class for Measures and Points subclasses across all Time Contexts.
	"""
	__slots__ = ()

	@classmethod
	def construct(typ,
		units, parts, start = 0,
		op = operator.add,
		Queue = collections.deque, int = int
	):
		d = Queue() # for opening containers
		popleft = d.popleft
		append = d.append
		prepend = d.appendleft

		terms = {}
		# Keyword processing. First, combine like terms.
		append(parts.items())

		containers = typ.context.containers
		convert = typ.context.convert
		getterm = typ.context.terms.get

		target_unit = typ.unit
		target_term = getterm(target_unit)
		total = start

		# currently containers can return containers,
		# thus this. :(
		while d:
			parts = popleft()
			for unit, value in parts:
				# a given unit is an expression of a "term".
				# years are an expression of months
				# seconds are an expression of days
				term = getterm(unit)

				if term is None:
					# not a term, assume that it's a container.
					prepend(containers[unit][1](typ, value)) # open container unit
				elif term == target_term:
					# simple conversion is needed for like-term units.
					total = op(total, convert(unit, target_unit, value))
				else:
					# not a like term. sum up all the unlike terms for later conversion.
					terms[term] = terms.get(term, 0) + convert(unit, term, value)

		# apply units
		for x in units:
			term = getterm(x.unit)
			if term == target_term:
				total = op(total, convert(x.unit, target_unit, (int(x) + x.datum)))
			else:
				terms[term] = terms.get(term, 0) + convert(x.unit, term, int(x))

		for term, value in terms.items():
			# first convert the existing total to the unlike-term units.
			# this gives context for the term's value.
			ctx = convert(target_unit, term, total)

			# maintain the difference (conversion remainder)
			dif = total - convert(term, target_unit, ctx)

			# apply the like term value to the ctx
			local = op(ctx, value)

			# convert both back to the target unit and
			# apply the difference to the actual total
			total = convert(term, target_unit, local) + dif
		return typ(int(total) - typ.datum)

	@classmethod
	def of(typ, *units, **parts):
		return typ.construct(units, parts)

	def update(self, part = None, replacement = None, of = None, align = 0):
		# adjust self by the difference of the new value and the selection.
		return self.construct((self,), {
			part: replacement - self.select(part, of = of, align = align)
		})

	def truncate(self, unit, int = int):
		term = self.context.terms[unit]
		if term == self.liketerm:
			# not need for datum-ized context
			c = self.context.convert(self.unit, unit, self)
			return self.__class__(self.context.convert(unit, self.unit, c.numerator // c.denominator))
		else:
			c = self.context.convert(self.unit, unit, self + self.datum)

		return self.construct((), {unit: c.numerator // c.denominator})

	def select(self, part, of = None, align = 0):
		if part in self.context.containers:
			# container type? no need for conversions. hook handles it
			return self.context.containers[part][0](self, of)
		elif of is None:
			# no of-whole? just convert and return
			r = self.context.convert(self.unit, part, self + self.datum)
			ir = int(r)
			return ir if ir == r else r.numerator // r.denominator

		convert = self.context.convert
		# A few significant factors in selection.
		this_unit = self.unit
		# What is the term of the part and of-whole?
		part_term = self.context.terms[part]
		of_term = self.context.terms[of]

		if of_term == self.liketerm:
			# The requested part is of the same term as the instance.
			# A simple modulus does the trick.
			boundary = convert(of, this_unit, 1)
			selection = self % boundary
		else:
			# the of_term is not a liketerm, convert self to the of_term.
			total = self + self.datum
			unlike_selection = convert(this_unit, of, total)

			if part_term == of_term:
				# the part term is the same as the of_term,
				# so get the base selection.
				boundary = convert(of, part, 1)
				selection = convert(of, part, unlike_selection) % boundary
				this_unit = part
			else:
				boundary = convert(of, this_unit, unlike_selection)
				selection = total - boundary

		if align:
			# after getting the selection
			offset = convert(part, this_unit, 1) * align
			selection = (selection + offset) % boundary

		return int(selection * self.context.compose(this_unit, part))

class Measure(Unit):
	__slots__ = ()

	@property
	def start(self):
		return self.__class__(0)

	@property
	def stop(self):
		return self

	def __neg__(self):
		return self.__class__(super().__neg__())

	def __abs__(self):
		return self.__class__(super().__abs__())

	def __str__(self):
		return str(self.select(self.unit))

	def __repr__(self, format = "{2}{0}.of({1})".format):
		# XXX: this is clearly stupid slow
		if self < 0:
			sign = '-'
			sub = -self
		else:
			sign = ''
			sub = self
		seq = self.context.measure_repr[self.liketerm]
		prev = None
		fields = []
		for x in seq:
			y = sub.select(x, prev)
			prev = x
			if y:
				sub = sub.elapse(**{x: -y})
				fields.append('{0}={1!s}'.format(x,y))
		return format(
			self.__name__,
			', '.join(fields),
			sign
		)

	def __contains__(self, t):
		return 0 <= t < self

	def elapse(self, *args, **parts):
		return self.of(self, *args, **parts)
	adjust = elapse

	def increase(self, *units, **parts):
		return self.construct(units, parts, start = self)

	def decrease(self, *units, **parts):
		return self.construct(units, parts, start = self, op = operator.sub)
abstract.Measure.register(Measure)

class Point(Unit):
	@property
	def start(self):
		return self

	@property
	def stop(self):
		return self.__class__(self + self.magnitude)

	def __contains__(self, t):
		c = self.context.convert(t.unit, self.unit, t)
		return (self.numerator // self.denominator) == (c.numerator // c.denominator)

	def __str__(self):
		# Python Classes are interfaces to units and terms defined in a context.
		# This Python method is intended to be implemented by a container.
		return self.select('__str__')

	def __repr__(self, format = "{0}.of(iso={1})".format):
		return format(self.__name__, repr(self.select('iso')))

	def rollback(self, *units, **parts):
		return self.construct(units, parts, start = self + self.datum, op = operator.sub)

	def elapse(self, *units, **parts):
		return self.construct(units, parts, start = self + self.datum)

	def measure(self, pit):
		return self.Measure(pit - self)
abstract.Measure.register(Point)

class Range(tuple):
	"""
	A range between two points, inclusive on the start, but non-inclusive on the end.

	If the start is greater than the end, the direction is implied to be
	negative.
	"""
	__slots__ = ()

	@property
	def magnitude(self):
		return abs(self.start.measure(self.stop))

	@property
	def direction(self):
		return self.start.measure(self.stop) // abs(self.magnitude)

	def __contains__(self, pit):
		# XXX: doesn't consider direction
		point = pit.measure(self.start)
		if point < 0:
			return False
		mag = self.stop.measure(self.start)
		return point < mag

	def __iter__(self):
		return self.points()

	@property
	def start(self):
		return self[0]

	@property
	def stop(self):
		return self[1]

	def points(self, step = None):
		"""
		Iterate through all the points between range according to the given step.
		"""
		start = self.start
		stop = self.stop

		if step is None:
			# default to the start's type
			step = start.Measure(start.magnitude)

		if stop >= start:
			# stop >= start
			pos = start
			while pos < stop:
				yield pos
				pos = pos.elapse(step)
		else:
			# stop < start
			pos = start
			while pos > stop:
				yield pos
				pos = pos.rollback(step)

class Context(object):
	"""
	A container for time units and transformations.

	.. warning:: **The APIs here are subject to change.**
	"""
	def __init__(self):
		# opaque transformations
		self.datums = {}
		self.terms = {} # grouping of like-terms
		self.bridges = {} # conversions between unlike-terms {(from, to): convert.__call__}
		self.ratios = {} # specifies ratios between like-terms (sometimes fractions)
		self.containers = {} # "terms" containing sets of terms.
		self.measures = {} # scalar types {term: type}
		self.measure_repr = {} # term to unit sequence to build out Scalar repr()
		self.points = {} # PointInTime types {unit: type}
		self.names = {} # unit names
		self.constants = {} # constant values used by the context. storage area

	def declare(self, id, datum):
		"""
		Declare a fundamental unit for use in a context.

		All defined, :py:meth:`rhythm.libunit.Context.define`, units are defined
		in terms of a declared unit.
		"""
		if not id.isidentifier():
			raise ValueError("unit names must be valid identifiers")

		self.ratios[id] = {id : fractions.Fraction(1,1)} # unit-to-unit is 1-to-1
		self.terms[id] = id
		self.measures[id] = {}
		self.points[id] = {}
		self.datums[id] = datum

	def define(self, id, term, exponent, base = 10):
		"""
		Defines a Unit in terms of another unit.
		"""
		if not id.isidentifier():
			raise ValueError("unit names must be valid identifiers")

		termu = self.terms[term]
		self.terms[id] = termu
		self.ratios[termu][id] = self.ratios[termu][term] * (base ** exponent)

	def bridge(self, from_unit, to_unit, transformer):
		"""
		Note a "bridge" between two units.

		In the case where a unit cannot not be resolved from its definitions,
		bridges can be used to perform the conversion.
		"""
		self.bridges[(from_unit,to_unit)] = transformer

	def container(self, id, pack, unpack):
		if not id.isidentifier():
			raise ValueError("container names must be valid identifiers")
		self.containers[id] = (pack, unpack)

	def constant(self, id, value):
		self.constants[id] = value

	@functools.lru_cache()
	def compose(self, from_unit, to_unit):
		"""
		Compose two ratios into another so that the `from_unit` can be converted
		into the `to_unit`.

		Ratio compositions are LRU cached.
		"""
		ratios = self.ratios[self.terms[from_unit]]
		r = ratios[from_unit] / ratios[to_unit]

		# If the integer version is equal, use it instead of the Fraction.
		ir = int(r)
		if ir == r:
			return ir
		else:
			return r

	def convert(self, from_unit, to_unit, value):
		"""
		Convert the `value` into `to_unit` from the `from_unit`.
		"""
		if from_unit in self.containers:
			# Containers have their own conversion implementation.
			pkg = self.containers[from_unit][1](value)
			return sum([
				self.convert(part, to_unit, value)
				for part, value in pkg
			])
		else:
			from_term = self.terms[from_unit]
			to_term = self.terms[to_unit]
			if from_term == to_term:
				# like terms, multiple by the composed ratio
				return value * self.compose(from_unit, to_unit)
			else:
				# unlike terms require a bridge in order to convert.
				# convert to bridge type, bridge, then from bridge type.
				bu = value * self.compose(from_unit, from_term)
				bdu = self.bridges[(from_term, to_term)](bu)
				return bdu * self.compose(to_term, to_unit)

	def new_measure_class(self, id, qname = None, default = False):
		Measure = self.measure_factory(id, qname)
		# ABC registration
		abstract.Time.register(Measure)
		# Associate with related unit.
		self.measures[Measure.liketerm][Measure.unit] = Measure
		if default:
			self.measures[Measure.liketerm][None] = Measure
		return Measure

	def new_point_class(self, Measure, qname = None, default = False):
		Point = self.point_factory(Measure, qname)
		# ABC registration
		abstract.Point.register(Point)
		# Associate with related unit.
		self.points[Point.liketerm][Point.unit] = Point
		if default:
			self.points[Point.liketerm][None] = Point
		return Point

	def datum_for_point(self, to_unit):
		r = self.convert(
			self.terms[to_unit], to_unit,
			self.datums[self.terms[to_unit]]
		)
		ir = r.numerator // r.denominator
		if ir == r:
			return ir
		return r

	def point_from_unit(self, unit):
		P = self.points[self.terms[unit]]
		if unit in P:
			return P[unit]
		return P[None]

	def measure_from_unit(self, unit):
		M = self.measures[self.terms[unit]]
		if unit in M:
			return M[unit]
		return M[None]

	def represent(self, term, unitseq):
		self.measure_repr[term] = unitseq

	def point_factory(self, Measure, qname, Class = Point, point_magnitude = 1):
		"""
		Construct a Point class from the given scalar.
		"""
		class Point(Class):
			__slots__ = ()
			__name__ = qname
			unit = Measure.unit
			name = Measure.name
			datum = self.datum_for_point(Measure.unit)
			# vector properties
			magnitude = point_magnitude # Vector is: Point -> Point+magnitude
			context = self
			liketerm = self.terms[Measure.unit]
		Point.Measure = Measure
		return Point

	def measure_factory(self, id, qname, Class = Measure, name = None, address = None):
		"""
		Construct a measure with the designated unit identifier and class.
		"""
		proper_name = name or id

		# Build constructors/classes for the parameterized unit.
		class Measure(Class):
			__slots__ = ()
			__name__ = qname
			unit = id
			name = proper_name
			datum = 0
			context = self
			liketerm = self.terms[id]
		return Measure

def standard_context(qname):
	"""
	Construct the standard time context from the modules in rhythm.
	"""
	from . import earth
	from . import metric
	from . import week
	from . import gregorian
	from . import libformat
	from . import libzone

	context = Context()

	# Most practical time units are actually related to a day.
	# Here, we declare the datum for day based PiTs
	context.declare('day', 5 * ((((365*4) + 1) * 100) - 3) + 1)
	# Likewise, Month PiTs are relative to Y2K
	context.declare('month', 2000*12)
	# NOTE: The month offset and day offset are *not* equal.
	#       Day offsets are relative to the beginning of the first week
	#       in Y2K in order to aid week updates.

	earth.context(context)
	gregorian.context(context)
	week.context(context)
	metric.context(context)
	libformat.context(context) # 'iso' and 'rfc' containers
	context.container('__str__', *context.containers['iso'])

	context.represent('day', [
		'petasecond',
		'annum',
		'week',
		'day',
		'hour',
		'minute',
		'second',
		'millisecond',
		'microsecond',
		'nanosecond',
	])

	context.represent('month', [
		'millennium',
		'century',
		'decade',
		'year',
		'month',
	])

	measures = (
		context.new_measure_class(
			'nanosecond', qname = (qname + '.Measure'), default = True),
		context.new_measure_class(
			'day', qname = qname + '.Days'),
		context.new_measure_class(
			'week', qname = qname + '.Weeks'),

		# gregorian month terms
		context.new_measure_class(
			'month', qname = qname + '.Months', default = True),
	)

	points = (
		context.new_point_class(
			measures[0], qname = qname + '.Timestamp', default = True),
		context.new_point_class(
			measures[1], qname = qname + '.Date'),
		context.new_point_class(
			measures[2], qname = qname + '.Week'),

		# gregorian month terms
		context.new_point_class(
			measures[3], qname = qname + '.GregorianMonth', default = True)
	)

	unix_delta = (
		points[0].datum - points[0].of(date=(1970,1,1)).measure(
			points[0].of(date=(2000,1,2))
		).select(points[0].unit)
	)

	# XXX: pretty much assuming the desired/possible precision of `x` here..
	def unpack_unix(typ, x, delta = unix_delta):
		return ('nanosecond', int(x * 1000000000) + delta),

	def pack_unix(pit, arg, delta = unix_delta):
		return (pit.select(pit.unit) - delta) / 1000000
	context.container('unix', pack_unix, unpack_unix)
	context.constant('unix', unix_delta)

	return (context, measures, points)
