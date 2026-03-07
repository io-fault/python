"""
# Route interface descriptions for &Path manipulations and &File system controls.

# [ File System Property Codes ]

# &File operations that analyze status properties use character codes to
# perform filtering. The codes listed here are primarily for POSIX file systems
# and may have extensions or different meanings when used with emulated file systems.

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
from typing import Protocol, TypeAlias, Type, IO
from contextlib import AbstractContextManager

Element: TypeAlias = tuple[str, Sequence['Element'], Mapping]

# Compatibility
import sys
if sys.version_info.major == 3 and sys.version_info.minor < 14:
	Path = object
	File = object
	FileStatus = object
del sys

@Hashable.register
class Path(Protocol):
	"""
	# Primitive operations for manipulating a sequence of identifiers.
	"""

	@property
	@abstractmethod
	def container(self) -> Path:
		"""
		# The route containing the resource identified by &self.

		# For file systems, this is the parent directory.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def absolute(self) -> list[Hashable]:
		"""
		# The absolute sequence of identifiers that make up the path.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def identifier(self) -> Hashable:
		"""
		# The identification of the resource relative to its immediate &container.
		# The last point in the route.
		"""
		raise NotImplementedError

	@abstractmethod
	def prefix(self, string:str):
		"""
		# Construct a new route with the given &prefix added to the beginning of the identifier.
		"""
		raise NotImplementedError

	@abstractmethod
	def suffix(self, string:str):
		"""
		# Construct a new route with the given &suffix added to the end of the identifier.
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
		# Construct a new route by extending &self with the points expressed in &path_expression.

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
		# Construct a new route by extending &self with a single &point.

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

class Status(Protocol):
	"""
	# Data class holding common file status fields.
	"""

	@property
	@abstractmethod
	def unit(self) -> str:
		"""
		# The unit that &size is measured with.

		# Presumed to be `'bytes'` for file systems, but may not be a concrete
		# measure of information storage for some systems.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def system(self) -> object:
		"""
		# System specific data structure holding the status data.
		# Usually &os.stat_result.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def size(self) -> int:
		"""
		# Count of &unit contained by the file.

		#!syntax/python
			assert (route.fs_size() == route.fs_status().size)
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def type(self) -> str:
		"""
		# String symbol identifying the type of file.

		# /`'void'`/
			# A broken link or nonexistent file.
		# /`'directory'`/
			# A file containing other files.
		# /`'data'`/
			# A regular file containing bytes.
		# /`'link'`/
			# Status record of a link to a file.
		# /`'pipe'`/
			# A named pipe; also known as a FIFO. (POSIX)
		# /`'socket'`/
			# A unix domain socket. (POSIX)
		# /`'device'`/
			# A character or block device file. (POSIX)
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def subtype(self) -> str|None:
		"""
		# For POSIX-type systems, designates the kind of (id)`device`:
		# (id)`block` or (id)`character`.

		# &None for status instances whose &type is not (id)`device`.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def executable(self) -> bool:
		"""
		# Whether the data file is considered executable by anyone.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def searchable(self) -> bool:
		"""
		# Whether the directory file is considered searchable by anyone.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def created(self):
		"""
		# Time of creation; UTC. Not available on all systems.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def last_modified(self):
		"""
		# Time of last modification; UTC.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def last_accessed(self):
		"""
		# Time of last access; UTC.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def meta_last_modified(self):
		"""
		# Time of last status change; UTC.
		"""
		raise NotImplementedError

class File(Path):
	"""
	# File system APIs for supporting common access functions.
	"""

	@property
	@abstractmethod
	def Status(self) -> Type[FileStatus]:
		"""
		# The status data structure used by the Path.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def Violation(self) -> Type[Exception]:
		"""
		# Exception describing the property violations found
		# by a call to &fs_require.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def filename(self) -> str:
		"""
		# File system specific alias for &identifier.
		"""
		raise NotImplementedError

	@property
	@abstractmethod
	def extension(self) -> str|None:
		"""
		# The last dot-extension of the filename.

		# &None if the filename has no `.` characters at all.
		"""
		raise NotImplementedError

	@abstractmethod
	def __pos__(self) -> File:
		"""
		# Resolve any relative path components, `.` and `..`, in &self.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_path_string(self) -> str:
		"""
		# Construct a normalized string representing the path to the file.

		# Relative resolution must still be explicitly performed, but empty
		# path entries delimiting partitions are eliminated.

		# &File protocol name suitable for use as `__fspath__` implementation.
		"""
		raise NotImplementedError

	@classmethod
	@abstractmethod
	def fs_tmpdir(Class) -> AbstractContextManager[File]:
		"""
		# Constuct a context manager that creates a temporary directory when entered.

		# On exit, the directory and its contents are destroyed.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_open(self, mode:str, buffering:int=-1, encoding:str=None, errors:str=None, newline=None) -> AbstractContextManager[IO]:
		"""
		# Open the file identified by the path, &self.

		# The file is opened when the returned context manager is entered and closed on exit.

		# The parameters match Python's &open builtin without `opener` and `closefd` where
		# the behavior is always the default.
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
	def fs_follow_links(self) -> Iterable[File]:
		"""
		# Follow the symbolic links back to the final non-link file.

		# The followed paths are not further resolved. Any links leading
		# to links or the final file will remain in the yielded paths.
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
	def fs_real(self) -> File:
		"""
		# Identify the portion of the route that actually exists on the file system.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_linear(self) -> File:
		"""
		# Identify the next non-linear directory.

		# Recursively scan the file system until a directory is found containing
		# zero files, more than one file, or a sole non-directory file is found.

		# [ Returns ]
		# The path to the next non-linear directory as a &File.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_status(self) -> Status:
		"""
		# Construct a data structure representing the latest status of the file.
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

		# [ Returns ]
		# - `'directory'`
		# - `'data'`
		# - `'pipe'`
		# - `'socket'`
		# - `'device'`
		# - `'void'`

		# If no file is present at the path or a broken link is present, `'void'` will be returned.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_size(self) -> int:
		"""
		# Return the size, count of bytes, of the file's content.

		# - `file.fs_size() == file.fs_status().size`
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
	def fs_since(self, time:object|None=None, inverse:bool=False) -> Iterable[File]:
		"""
		# Select data files within the path, &self, whose modification time exceeds &time.

		# [ Parameters ]
		# /time/
			# The referennce time. When unspecified as &None, the modification time
			# of the directory identified by &self is used.
		# /inverse/
			# Select files modified before &time when &True.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_modified(self):
		"""
		# Update the modification time of the file identified by &self.

		# The new modification time should reflect the real clock's status on the system
		# managing the file.
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
			# The maximum file system depth to descend from &self.
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

	@abstractmethod
	def fs_iterfiles(self, /, type:(str|None)=None) -> Iterable[File]:
		"""
		# Generate &File instances identifying the files held by the directory, &self.
		# By default, all file types are included, but if the &type parameter is given,
		# only files of that type are returned.

		# If &self is not a directory or cannot be searched, an empty iterator is returned.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_list(self, type:str='data') -> tuple[list[File], list[File]]:
		"""
		# Retrieve the list of files contained by the directory referred to by &self.
		# Returns a pair, the sequence of directories and the sequence of data files.

		# Sockets, pipes, devices, and other non-data files are not retained in the list.
		"""
		raise NotImplementedError

	@abstractmethod
	def fs_index(self, type:str='data') -> Iterable[tuple[File, list[File]]]:
		"""
		# Generate pairs of directories associated with their files.

		# Sockets, pipes, devices, broken links, and other non-data files are not retained in the lists.
		"""
		raise NotImplementedError
