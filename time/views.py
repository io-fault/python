"""
# Access to timezone views for adjusting timestamps in and out of local forms.

# Usage:

#!syntax/python
	from fault.time import types, views
	z = views.Zone.open(types.from_unix_timestamp, "America/Los_Angeles")
"""
import os
import os.path
import functools
from . import tzif
from . import abstract

class Zone(object):
	"""
	# An ordered sequence of transition times whose ranges correspond to a
	# particular offset.

	# [ Properties ]
	# /default/
		# The default &Offset of the &Zone.
	"""

	class Offset(tuple):
		"""
		# Offsets are constructed by a tuple of the form: `(offset, abbreviation, type)`.
		# Primarily, the type signifies whether or not the offset is daylight
		# savings or not.

		# &Offset instances are usually extracted from &Zone objects which
		# build a sequence of transitions for subsequent searching.
		"""
		__slots__ = ()

		unit = 'second'
		datum = 0

		@property
		def magnitude(self):
			"""
			# The offset in seconds from UTC.
			"""
			return self[0]

		@property
		def abbreviation(self):
			"""
			# The Offset's timezone abbreviation; such as UTC, GMT, and EST.
			"""
			return self[1]

		@property
		def type(self):
			"""
			# Field used to identify if the &Offset is daylight savings time.
			"""
			return self[2]

		@property
		def is_dst(self):
			"""
			# Whether or not the &Offset is referring to a daylight savings time
			# offset.
			"""
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
			# Return the offset-qualified ISO representation of the given point in time.
			"""
			return ' '.join((pit.select('iso'), str(self)))

		@classmethod
		def from_tzinfo(Class, tzinfo):
			"""
			# Construct a Zone instance from a &.tzif.tzinfo tuple.
			"""
			return Class(
				(
					tzinfo.tz_offset,
					tzinfo.tz_abbrev.decode('ascii'),
					'dst' if tzinfo.tz_isdst else 'std',
				)
			)

	abstract.Measure.register(Offset)

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

	import bisect
	def find(self, pit, search=bisect.bisect):
		"""
		# Get the appropriate offset in the zone for a given Point In Time, &pit.
		# If the &pit does not fall within a known range, the &default will be returned.

		# Returns an offset for the timestamp according to the Zone's transition times.

		# [ Parameters ]
		# /pit/
			# The &.library.Timestamp to use to find an offset with.
		"""
		idx = search(self.transitions, pit) - 1
		try:
			z = self.offsets[idx]
		except IndexError:
			z = self.default
		return z

	def slice(self, start, stop, search=bisect.bisect):
		"""
		# Get a slice of transition points and time zone offsets
		# relative to a given &start and &stop.

		# Returns an iterable of transitions and &Offset instances that have
		# occurred during the period designated by the slice.

		# [ Parameters ]
		# /start/
			# The start of the period.
		# /stop/
			# The end of the period.
		"""
		first_offset = search(self.transitions, start) - 1
		last_offset = search(self.transitions, stop)

		trans = self.transitions[first_offset:last_offset]
		offs = self.offsets[first_offset:last_offset]

		return zip(trans, offs)
	del bisect

	def localize(self, pit):
		"""
		# Given &pit, return the localized version according to the zone's transitions.

		# The given Point In Time is expected to have a perspective consistent with the zone's
		# transition times. (In the same zone.)

		# Returns the localized timestamp.

		# [ Parameters ]
		# /pit/
			# The timestamp to localize.
		"""
		offset = self.find(pit)
		return (pit.elapse(offset), offset)

	def normalize(self, offset, pit):
		"""
		# This function should be used in cases where adjustments are being made to
		# an already zoned point in time. Once the adjustments are complete, the point should be
		# normalized in order to properly represent the local point.

		# If no change is necessary, the exact, given &pit will be returned.

		# Returns the re-localized &pit and its new &Offset in a tuple.

		# [ Parameters ]
		# /offset/
			# The offset of the &pit.
		# /pit/
			# The localized point in time to normalize.
		"""
		p = pit.rollback(offset)

		new_offset = self.find(p)
		# Using 'is' because it is possible for offsets to be equal, but different.
		if offset is new_offset:
			# no adjustment necessary
			return (pit, offset)
		return (p.elapse(new_offset), new_offset)

	@classmethod
	def from_tzif_data(Class, construct, tzd, name = None, lru_cache = functools.lru_cache):
		# Re-use prior created offsets.
		zb = lru_cache(maxsize=None)(Class.Offset.from_tzinfo)

		# convert the unix epoch timestamps in seconds to Y2K+1 in nanoseconds
		offsets, transitions, leaps = tzd

		transition_offsets = [zb(x[1]) for x in transitions]
		transition_points = [construct(x[0]) for x in transitions]

		default = offsets[0]

		return Class(transition_points, transition_offsets, zb(default), leaps, name)

	@classmethod
	def from_file(Class, construct, filepath):
		return Class.from_tzif_data(
			construct,
			tzif.get_timezone_data(filepath),
			name = filepath
		)

	@classmethod
	def open(Class, construct, fp = None, _fsjoin = os.path.join):
		if not fp:
			fp = os.environ.get(tzif.tzenviron)

		if not fp:
			fp = tzif.tzdefault
		else:
			fp  = _fsjoin(tzif.tzdir, fp)

		return Class.from_file(construct, fp)
