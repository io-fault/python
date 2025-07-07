"""
# Function and iterator tools used by local projects.
"""
import functools
import itertools
import typing
import dataclasses

cachedcalls = functools.lru_cache
partial = functools.partial

def nothing(*args, **kw) -> None:
	"""
	# Callable that returns &None regardless of the arguments and keywords given.
	"""
	pass

def reflect(obj):
	"""
	# Callable that returns the single argument that it was given.
	"""
	return obj

# Create the dataclass constructor commonly used by fault projects.
try:
	reflect(dataclasses.dataclass(slots=True))
except TypeError:
	# Pre-3.10
	record = struct = partial(dataclasses.dataclass, eq=True, frozen=True)
else:
	record = struct = partial(dataclasses.dataclass, slots=True, eq=True, frozen=True)

@cachedcalls(16)
def constant(obj, partial=partial):
	"""
	# Return a callable that returns the given object regardless of
	# the given parameters.
	"""

	if obj is None:
		return nothing
	else:
		return partial(reflect, obj)

def unique(iterable, *existing, set=set):
	"""
	# Iterate through the contents of the &iterable,
	# but only allow an item to be emitted once.

	# ! WARNING:
		# The implementation uses a &set to track which items have transpired.
		# It is never reset internally, so the generator can allocate
		# arbitrary quantities of memory.

	# [ Parameters ]

	# /iterable/
		# The iterable whose duplicate items should be eliminated.
	# /existing/
		# The initial items in the filter set. Arguments given as
		# &existing will never be emitted. For instance, filtering
		# &None may be common.
	"""

	xs = set(existing)
	add = xs.add
	del existing

	for x in iterable:
		if x in xs:
			continue
		add(x)
		yield x

def interlace(*iters, next=next, cycle=itertools.cycle, map=map):
	"""
	# An iterator constructor that takes a sequence of
	# iterables and interlaces their items one after another.
	# While uncommon, the pattern produced by interlace is complicated
	# enough that forcing its recreation is undesirable.

	# Interlace produces an iterator following the pattern:

	#!text
		interlace(i1, i2, ..., in) -> (
			i1-0, i2-0, ..., in-0,
			i1-1, i2-1, ..., in-1,
			⋮
			i1-n, i2-n, ..., in-n,
		)
	"""

	return map(next, cycle([iter(x) for x in iters]))

def compose(*callables,
		str=str, len=len, dict=dict, zip=zip, exec=exec, range=range,
		_model = ("def Composition(x,", "):\n\treturn ")
	):
	"""
	# Return a composition of the given callable arguments.

	# Executing a composition is equivalent to: `g(f(x))` where
	# g and f are the parameters to compose: `compose(g,f)(x)`.

	# Compose has some trivial intelligence in that compositions
	# of single functions return the function and compositions
	# of no functions returns &reflect.

	# The resulting composition exposes the callables on the
	# function's "callables" attribute.
	"""

	# not necessary, but let's avoid creating superfluous
	# function objects for compose() and compose(f)
	nargs = len(callables)

	if not nargs:
		# no transformation is a reflection
		return reflect
	elif nargs == 1:
		# not composition necessary
		return callables[0]

	names = ['f' + str(i) for i in range(nargs)]
	flocals = dict(zip(names, callables))
	code = _model[0] + ','.join(['='.join((y,y)) for y in names]) + _model[1]
	code = code + '('.join(names) + '(x)' + (')' * (nargs-1))
	flocals['__name__'] = "<function-composition>"
	exec(code, flocals, flocals)
	composition = flocals["Composition"]
	composition.callables = callables

	return composition

def plural(f):
	"""
	# Create a function that pluralizes the return of the given callable, &f.
	"""

	return (lambda x: (f(x),))

def unroll(f, Sequence=list, map=map):
	"""
	# Given a callable taking a single parameter, create another
	# that maps the callable against a sequence.

	# Equivalence:
	#!syntax/python
		unroll(f)(iterable) == [f(x) for x in iterable]
	"""

	return compose(Sequence, partial(map, f))

sum_lengths = compose(sum, partial(map, len))

def group(condition, iterable, initial=None, Sequence=list):
	"""
	# Structure the given &iterable by the given &condition.
	# Returns a generator producing (grouping, sequence) pairs.

	# A &True result from &condition essentially terminates the subsequence,
	# and creates a new sequence to be populated while &condition is &False.

	# [ Parameters ]

	# /condition/
		# The grouping item in the tuple is the item that triggers
		# a &True result from &condition.

	# /iterable/
		# The sequence item in the tuple is a sequence of items
		# where the result of the &condition was &False.

	# /initial/
		# Designate the initial grouping to be emitted.
		# Defaults to &None.
	"""

	grouping = initial
	contents = Sequence()
	for item in iterable:
		if condition(item):
			yield (grouping, contents)
			grouping = item
			contents = Sequence()
		else:
			contents.append(item)

	yield (grouping, contents)

class cachedproperty(object):
	"""
	# Attribute override for immutable property methods.

	# Presumes the wrapped method name is consistent with the property name.
	"""

	def __init__(self, method, doc=None):
		self.method = method
		self.name = method.__name__
		self.__doc__ = doc or method.__doc__

	def __get__(self, instance, Class):
		if instance is None:
			return self
		instance.__dict__[self.name] = result = self.method(instance)
		return result

def consistency(*iterables,
		takewhile=itertools.takewhile,
		zip=zip, sum=sum, len=len, set=set
	) -> int:
	"""
	# Return the level of consistency among the elements produced by the given &iterables.
	# The counting stops when an element is not equal to the others at the same index.

	# More commonly, the common prefix depth or length of all the given iterables.
	# Elements must be hashable; equality is indirectly performed by forming a set.
	"""
	return sum(
		takewhile(
			(1).__eq__,
			(len(set(x)) for x in zip(*iterables))
		)
	)
