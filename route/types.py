"""
# Segment and Selector implementation access.
"""
import itertools
from . import core
from . import rewrite

consistency = core.consistency # Ultimately from fault.context.tools

class Segment(core.PartitionedSequence[core.Identifier]):
	"""
	# Sequence of identifiers that may be incorporated into a selector subclass.
	"""

	__slots__ = ('context', 'points',)

	def __str__(self):
		parts = ["->".join(x) for x in self.iterpartitions()]
		return ''.join("(" + x + ")" for x in parts)

	def __bool__(self):
		"""
		# True is the segment has any points; False if zero.
		"""
		for x in self.iterpartitions():
			if x:
				return True

		return False

	def segment(self, from_stem=None,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		):
		if self.context is from_stem:
			return Cache(self.__class__, None, self.points)
		elif from_stem is None:
			return self

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(self.__class__, None, ())

		return self.__class__(None, seg[cl:])

class Selector(core.PartitionedSequence[core.Identifier]):
	"""
	# Route domain base class.

	# Subclasses provide access methods to a resource identified
	# by the sequence of identifiers contained within the selector instance.
	"""

	def segment(self, from_stem=None,
			Segment=Segment,
			Cache=core.construct_cache,
			RPath=core.relative_path,
		) -> Segment:
		"""
		# Construct a &Segment from &self starting at the position designated by &from_stem.
		# If stem is not given, the entire selector will be converted.
		"""
		if self.context is from_stem:
			return Cache(Segment, None, self.points)
		elif from_stem is None:
			return Segment.from_partitions(self.partitions())

		cl, l, seg = RPath(self, from_stem)
		if cl < l:
			# Outside of stem.
			return Cache(Segment, None, ())

		return Segment(None, seg[cl:])

	def __str__(self):
		parts = ["/".join(x) for x in self.iterpartitions()]
		return ''.join("[" + x + "]" for x in parts)

	def __bool__(self):
		# Subclasses with another opinion on selector truth should override.
		return True

	_relative_resolution = staticmethod(rewrite.relative)

	def suffix(self, delta):
		return self * (self.identifier + delta)

	def prefix(self, delta):
		return self * (delta + self.identifier)

class RequirementViolation(Exception):
	"""
	# Exception raised by &.abstract.Path.fs_require when requirements are not met.

	# [ Properties ]
	# /r_violation/
		# The subtype declaring the kind of violation that occurred.
		# /`'void'`/
			# File did not exist.
		# /`'inaccessible'`/
			# Path traversed through a non-directory file,
			# or had insufficient permissions on the leading path.
		# /`'type'`/
			# The &r_type did not match the &fs_type.
		# /`'directory'`/
			# The file identified by the path is a directory.
		# /`'prohibited'`/
			# The required permissions stated in &r_properties
			# were not available to the process.
	# /r_type/
		# The required type issued to &.abstract.Path.fs_require.
	# /r_properties/
		# The required properties issued to &.abstract.Path.fs_require.
	# /fs_type/
		# The type of the file identified by &.abstract.Path.fs_type.
	# /fs_path/
		# The path to the subject file.
	# /type_codes/
		# The character codes used by &.abstract.Path.fs_require;
		# also defined by &.abstract.Types
	"""

	type_codes = {
		'*': None,
		'/': 'directory',
		'.': 'data',
		'#': 'device',
		'@': 'socket',
		'|': 'pipe',
		'&': 'link',
		'!': 'void',
		'?': 'unknown',
	}

	def __init__(self, subject, type, violation, rtype, properties):
		self.fs_path = subject
		self.fs_type = type

		self.r_violation = violation
		self.r_type = rtype
		self.r_properties = properties

	def __str__(self):
		rv = self.r_violation
		path = f"PATH[{self.fs_type}]: {self.fs_path!s}"

		if rv == 'type':
			desc = f"not a {self.r_type!r} file"
		elif rv == 'directory':
			desc = "file is a directory"
		elif rv == 'void':
			desc = "file not does not exist"
		elif rv == 'prohibited':
			desc = "file does not have the necessary permissions"
		elif rv == 'inaccessible':
			desc = "file could not accessed"
		else:
			desc = rv

		return f"{desc}\n{path}"
