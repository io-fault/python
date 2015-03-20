"""
Timezone support.
"""
import os
import os.path
import bisect
import functools
from . import tzif
from . import abstract

class Offset(tuple):
	"""
	Offsets are constructed by a tuple of the form: `(offset, abbreviation, type)`.
	Primarily, the type signifies whether or not the offset is daylight
	savings or not.

	:py:class:`Offset` instances are usually extracted from :py:class:`Zone` objects which
	build a sequence of transitions for subsequent searching.
	"""
	__slots__ = ()

	unit = 'second'
	datum = 0

	@property
	def magnitude(self):
		return self[0]

	@property
	def abbreviation(self):
		return self[1]

	@property
	def type(self):
		return self[2]

	@property
	def is_dst(self):
		"Returns: `self.type == 'dst'`"
		return self.type == 'dst'

	def __hash__(self):
		return self[0].__hash__()

	def __str__(self):
		return '%s%s%d' %(
			self.abbreviation,
			"+" if self.magnitude >= 0 else "-",
			abs(self.magnitude)
		)

	def __repr__(self):
		return '<%s(%s: %d)>' %(self.__class__.__name__, self.abbreviation, self.magnitude)

	def __eq__(self, ob):
		return tuple(self) == tuple(ob)

	def __int__(self):
		return self.magnitude

	def iso(self, pit):
		"""
		Return the offset-qualified ISO representation of the given point in time.
		"""
		return ' '.join((pit.select('iso'), str(self)))

	@classmethod
	def from_tzinfo(typ, tzinfo):
		"""
		Construct a Zone instance from a :py:class:`.tzif.tzinfo` tuple.
		"""
		return typ(
			(
				tzinfo.tz_offset,
				tzinfo.tz_abbrev.decode('ascii'),
				'dst' if tzinfo.tz_isdst else 'std',
			)
		)
abstract.Measure.register(Offset)

class Zone(object):
	"""
	Zones consist of a sequence of transition times whose ranges correspond to a
	particular offset.

	A mapping of transition times to their corresponding offset.

	:py:class:`Zone` instances manage the selection of a particular
	:py:class:`Offset`.
	"""

	def __init__(self, transitions, offsets, default, leaps, name):
		self.transitions = transitions
		self.offsets = offsets
		self.default = default
		self.leaps = leaps
		self.name = name

	def __repr__(self):
		return '<%s: %s[%d/%d]>' %(
			self.__class__.__name__,
			self.name,
			len(self.transitions),
			len(self.offsets),
		)

	def find(self, pit, bisect = bisect.bisect):
		"""
		find(pit)

		:param pit: The timestamp to use to find an offset with.
		:returns: An offset for the timestamp according to the Zone's transition times.
		:rtype: :py:class:`Offset`

		Get the appropriate offset in the zone for a given Point In Time, `pit`.

		If the `pit` does not fall within a known range, the `default` will be returned.
		"""
		idx = bisect(self.transitions, pit) - 1
		try:
			z = self.offsets[idx]
		except IndexError:
			z = self.default
		return z

	def slice(self, start, stop, bisect = bisect.bisect):
		"""
		slice(start, stop)

		:param start: The start of the period.
		:type start: :py:class:`.abstract.Point`
		:param stop:  The end of the period.
		:type stop: :py:class:`.abstract.Point`
		:returns: A sequence of offsets, transitions, that have occurred during the period.
		:rtype: [:py:class:`Offset`]

		Get a slice of transition points and time zone offsets relative to a given `start` and `stop`.
		"""
		first_offset = bisect(self.transitions, start) - 1
		last_offset = bisect(self.transitions, stop)

		trans = self.transitions[first_offset:last_offset]
		offs = self.offsets[first_offset:last_offset]

		return zip(trans, offs)

	def localize(self, pit):
		"""
		:param pit: The timestamp to localize.
		:returns: The localized timestamp.
		:rtype: :py:class:`.abstract.Point`

		Given a `pit`, return the localized version according to the zone's transitions.

		The given Point In Time is expected to have a perspective consistent with the zone's
		transition times. (In the same zone.)
		"""
		offset = self.find(pit)
		return (pit.elapse(offset), offset)

	def normalize(self, offset, pit):
		"""
		:param offset: The offset of the `pit`.
		:param pit: The localized point in time to normalize.
		:returns: The re-localized `pit` and it's new offset in a tuple.
		:rtype: (:py:class:`.abstract.Point`, :py:class:`Offset`)

		This function should be used in cases where adjustments are being made to
		an already zoned point in time. Once the adjustments are complete, the point should be
		normalized in order to properly represent the local point.

		If no change is necessary, the exact, given `pit` will be returned.
		"""
		p = pit.rollback(offset)

		new_offset = self.find(p)
		# Using 'is' because it is possible for offsets to be equal, but different.
		if offset is new_offset:
			# no adjustment necessary
			return (pit, offset)
		return (p.elapse(new_offset), new_offset)

	@classmethod
	def from_tzif_data(typ, construct, tzd, name = None, lru_cache = functools.lru_cache):
		# Re-use prior created offsets.
		zb = lru_cache(maxsize=None)(Offset.from_tzinfo)

		# convert the unix epoch timestamps in seconds to Y2K+1 in nanoseconds
		offsets, transitions, leaps = tzd

		transition_offsets = [zb(x[1]) for x in transitions]
		transition_points = [construct(x[0]) for x in transitions]

		default = offsets[0]

		return typ(transition_points, transition_offsets, zb(default), leaps, name)

	@classmethod
	def from_file(typ, construct, filepath):
		return typ.from_tzif_data(
			construct,
			tzif.get_timezone_data(filepath),
			name = filepath
		)

	@classmethod
	def open(typ, construct, fp = None, _fsjoin = os.path.join):
		if not fp:
			fp = os.environ.get(tzif.tzenviron)

		if not fp:
			fp = tzif.tzdefault
		else:
			fp  = _fsjoin(tzif.tzdir, fp)

		return typ.from_file(construct, fp)
