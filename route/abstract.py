"""
# Route interface descriptions for &Path manipulations and &File system controls.

# [ File System Property Codes ]

# &File operations that analyze status properties use character codes to
# perform filtering. The codes listed here are primarily for POSIX filesystems
# and may have extensions or different meanings when used with emulated filesystems.

# [> Permissions]
# Character codes identifying available permissions.

	# /`'r'`/
		# Readable.
	# /`'w'`/
		# Writable.
	# /`'x'`/
		# Executable or searchable.

# [> Types]
# Character codes identifying a type of file.

	# /`'*'`/
		# Any.
	# /`'!'`/
		# Void; file must not exist.
	# /`'/'`/
		# Directory.
	# /`'.'`/
		# Data. A "regular" file.
	# /`'&'`/
		# A symbolic link.
	# /`'|'`/
		# A named pipe.
	# /`'@'`/
		# A file system socket file.
	# /`'#'`/
		# A device file.
	# /`'?'`/
		# Unknown type.
		# File exists, but it's type is not known and may be inaccessible.
"""
from abc import abstractmethod
from collections.abc import Hashable, Iterable, Sequence, Mapping
from typing import Protocol, TypeAlias, Type

Element: TypeAlias = tuple[str, Sequence['Element'], Mapping]

@Hashable.register
class Path(Protocol):
	"""
	# Primitive operations for manipulating a sequence of identifiers.
	"""

	@property
	@abstractmethod
	def container(self) -> Path:
		"""
		# The route containing the final identifier in &self.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def absolute(self) -> list[Hashable]:
		"""
		# The absolute sequence of identifiers.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def identifier(self) -> Hashable:
		"""
		# The object identifying the resource relative to its immediate container.
		# The last point in the route.
		"""
		raise NotImplementedError

	@abstractmethod
	def truncate(self, identifier:Hashable) -> Path:
		"""
		# Construct a new route consisting of the existing sequence of points up to the *last*
		# point specified by the &point argument. Similar to slicing a sequence from a
		# reverse index search.
		"""
		raise NotImplementedError

	@abstractmethod
	def __invert__(self) -> Iterable[Path]:
		"""
		# Stepwise root ascension.

		#!python
			assert list(~route) == [route ** 1, route ** 2, ..., route ** len(route)]
		"""
		raise NotImplementedError

	@abstractmethod
	def __lshift__(self, route:Path) -> Iterable[Path]:
		"""
		# Stepwise ascension path.
		"""
		raise NotImplementedError

	@abstractmethod
	def __rshift__(self, route:Path) -> Iterable[Path]:
		"""
		# Stepwise descension path.
		"""
		raise NotImplementedError

	@abstractmethod
	def __xor__(self, route:Path) -> Iterable[Path]:
		"""
		# Stepwise traverse path.
		"""
		raise NotImplementedError

	@abstractmethod
	def __matmul__(self, path_expression:str) -> Path:
		"""
		# Composite extension.
		# Construct a new route by extending &self with the points expressed in &path.

		# [ Parameters ]
		# /path_expression/
			# A string that represents a relative or absolute path.
		"""
		raise NotImplementedError

	@abstractmethod
	def __add__(self, points:Iterable[Hashable]) -> Path:
		"""
		# Extension by iterable.
		# Construct a new route by extending &self with &points.

		#!python
			assert (route + points) == (route / points[0] / points[1] ... / points[n])
		"""
		raise NotImplementedError

	@abstractmethod
	def __floordiv__(self, route:Path) -> Path:
		"""
		# Segment extension.
		# Construct a new route by extending &self with all the points in &route.

		#!python
			assert (route // segment) == (route + segment.absolute)
		"""
		raise NotImplementedError

	@abstractmethod
	def __truediv__(self, point:Hashable) -> Path:
		"""
		# Single extension.
		# Construct a new route by extending &self with the sole &point.

		#!python
			assert (route / identifier) == (route + [identifier])
		"""
		raise NotImplementedError

	@abstractmethod
	def __mul__(self, identifier:Hashable) -> Path:
		"""
		# Identifier substitution.
		# Construct a new route by extending &self.container with &identifier.

		#!python
			assert (route * 'replacement') == (route.container / 'replacement')
		"""
		raise NotImplementedError

	@abstractmethod
	def __pow__(self, nth) -> Path:
		"""
		# Numeric ascension operation.
		# Construct a new route representing the &nth container of &self.

		#!python
			assert (route ** 1) == (route.container)
			assert (route ** 2) == (route.container.container)
		"""
		raise NotImplementedError

class File(Path):
	"""
	# File system APIs for supporting common access functions.
	"""

	@property
	@abstractmethod
	def Violation(self) -> Type[Exception]:
		"""
		# Exception describing the property violations found
		# by a call to &fs_require.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_require(self, properties:str, *, type=None):
		"""
		# Check the file for the expressed requirements.
		# The &properties string consists of characters described by
		# &[File System Property Codes].

		# [ Parameters ]
		# /properties/
			# The required type, permissions and option control flags.
		# /type/
			# The required file type, inclusive.
			# When &None, the default, the file type must not be a directory.

			# Overrides any file type codes present in &properties.

		# [ Exceptions ]
		# /&Violation/
			# Raised when a designated property is not present on the file.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_replace(self, replacement):
		"""
		# Destroy the existing file or directory, &self, and replace it with the
		# file or directory at the given route, &replacement.

		# [ Parameters ]
		# /replacement/
			# The route to the file or directory that will be used to replace
			# the one at &self.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_void(self):
		"""
		# Destroy the file or directory at the location identified by &self.
		# For directories, this recursively removes content as well.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_reduce(self, discarded):
		"""
		# Relocate the directory contents in &discarded into &self, and
		# destroy the segment of directories between &self and &discarded.

		# [ Returns ]
		# &self
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_alloc(self):
		"""
		# Allocate the necessary resources to create the target path as a file or directory.

		# Normally, this means creating the *leading* path to the identified resource.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_link_relative(self, path):
		"""
		# Create or update a *symbolic* link at &self pointing to &path, the target file.
		# The linked target path will be relative to &self' route.

		# [ Parameters ]
		# /path/
			# The route identifying the target path of the symbolic link.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_link_absolute(self, path):
		"""
		# Create or update a *symbolic* link at &self pointing to &path, the target file.
		# The linked target path will be absolute.

		# [ Parameters ]
		# /path/
			# The route identifying the target path of the symbolic link.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_mkdir(self):
		"""
		# Create a directory at the location referenced by &self.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_select(self, properties:str='*') -> Iterable[File]:
		"""
		# Select the set of files contained within the directory identified by &self
		# that match the required &properties.

		# The &properties string consists of characters described by
		# &[File System Property Codes].
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_real(self) -> File:
		"""
		# Identify the portion of the route that actually exists on the filesystem.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_linear(self) -> File:
		"""
		# Identify the next non-linear directory.

		# Recursively scan the filesystem until a directory is found containing
		# zero files, more than one file, or a sole non-directory file is found.

		# [ Returns ]
		# The path to the next non-linear directory as a &File.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_status(self):
		"""
		# Construct a data structure representing the latest status of the file.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_update(self, *,
			name=None, size=None,
			created=None, modified=None,
		):
		"""
		# Update the status properties of the file identified by &self.
		# If no arguments are supplied, not changes will be performed.

		# [ Parameters ]
		# /name/
			# Change the identifier used to select the file relative to
			# its parent directory.
		# /size/
			# Adjust the size of the file, truncating or zero-padding as needed.
		# /modified/
			# The time that the file was said to be modified.
		# /created/
			# The time that the file was said to be created.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_load(self) -> bytes:
		"""
		# Retrieve the binary data stored at the location identified by &self.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_store(self, data:bytes):
		"""
		# Store the given &data at the location referenced by &self.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_type(self) -> str:
		"""
		# A string identifying the type of file selected by the &Route.
		# Often a shorthand for accessing the type from the structure
		# returned by &fs_status.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_executable(self) -> bool:
		"""
		# Whether or not the regular file is executable.

		# Directories marked as executable are not considered executables.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_searchable(self) -> bool:
		"""
		# Whether or not the directory's listing can be retrieved.

		# Regular files marked as executable are not considered searchable.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_snapshot(self) -> Sequence[Element]:
		"""
		# Construct an element tree of files from the directory identified by &self.

		# Exceptions raised by operations populating the tree are trapped
		# as `'exception'` elements that are filtered by &process by default.

		# [ Parameters ]
		# /process/
			# Boolean callable determining whether or not a file should be included in the
			# resulting element tree.

			# Defaults to a function excluding `'exception'` types.
		# /depth/
			# The maximum filesystem depth to descend from &self.
			# If &None, no depth constraint is enforced.
			# Defaults to `8`.
		# /limit/
			# The maximum number of elements to accumulate.
			# If &None, no limit constraint is enforced.
			# Defaults to `2048`.

		# [ Returns ]
		# The sequence of elements that represent the directory's listing
		# according to the given arguments.
		"""
		raise NotImplementedError
