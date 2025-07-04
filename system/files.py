"""
# Filesystem interfaces and data structures.

# Current working directory related interfaces are provided in &.process.

# [ Elements ]
# /root/
	# The &Path to the root directory of the operating system.
# /null/
	# The &Path to the file that has no content and will discard writes.
# /empty/
	# The &Path to the directory that contains no files.
# /type_codes/
	# Single character representations for file types.
	# Primarily used by &Path.fs_require.
"""
from collections.abc import Sequence, Iterable
from typing import Optional, TypeAlias
import os
import os.path
import sys
import contextlib
import collections
import stat
import itertools
import functools

# Moving to cached class properties.
import shutil
import tempfile

from ..context.tools import cachedcalls
from ..route.types import Selector, Segment

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

class RequirementViolation(Exception):
	"""
	# Exception raised by &Path.fs_require when requirements are not met.

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
		# The required type issued to &Path.fs_require.
	# /r_properties/
		# The required properties issued to &Path.fs_require.
	# /fs_type/
		# The type of the file identified by &fs_path.
	# /fs_path/
		# The path to the subject file.
	"""

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

class Status(tuple):
	"""
	# File status interface providing symbolic names for the data packed in
	# the system's status record, &system.

	# [ Engineering ]
	# Experimental. Helps isolate delayed imports.
	# Likely undesired noise if a stat-cache is employed by &Path.
	"""
	__slots__ = ()

	_fs_type_map = {
		stat.S_IFIFO: 'pipe',
		stat.S_IFLNK: 'link',
		stat.S_IFREG: 'data',
		stat.S_IFDIR: 'directory',
		stat.S_IFSOCK: 'socket',
		stat.S_IFBLK: 'device',
		stat.S_IFCHR: 'device',
	}

	_fs_subtype_map = {
		stat.S_IFBLK: 'block',
		stat.S_IFCHR: 'character',
	}

	@property
	def _interpret_time(self):
		from ..time.system import _unix
		self.__class__._interpret_time = staticmethod(_unix)
		return _unix

	@property
	def _read_user(self):
		from pwd import getpwuid
		self.__class__._read_user = staticmethod(getpwuid)
		return getpwuid

	@property
	def _read_group(self):
		from grp import getgrgid
		self.__class__._read_group = staticmethod(getgrgid)
		return getgrgid

	@classmethod
	def from_route(Class, route):
		return Class((os.stat(route), route.identifier))

	@property
	def system(self):
		"""
		# The status record produced by the system (&os.stat).
		"""
		return self[0]

	@property
	def filename(self) -> str:
		"""
		# The name of the file.
		"""
		return self[1]

	def __add__(self, operand):
		# Protect from unexpected addition.
		# tuple() + Status(...) is still possible.
		return NotImplemented

	@property
	def size(self) -> int:
		"""
		# Number of bytes contained by the file.
		"""
		return self.system.st_size

	@property
	def type(self, ifmt=stat.S_IFMT) -> str:
		"""
		# /`'void'`/
			# A broken link or nonexistent file.
		# /`'directory'`/
			# A file containing other files.
		# /`'data'`/
			# A regular file containing bytes.
		# /`'pipe'`/
			# A named pipe; also known as a FIFO.
		# /`'socket'`/
			# A unix domain socket.
		# /`'device'`/
			# A character or block device file.
		# /`'link'`/
			# Status record of a link to a file.
		"""
		return self._fs_type_map.get(ifmt(self.system.st_mode), 'unknown')

	@property
	def subtype(self, *, ifmt=stat.S_IFMT) -> Optional[str]:
		"""
		# For POSIX-type systems, designates the kind of (id)`device`:
		# (id)`block` or (id)`character`.

		# &None for status instances whose &type is not (id)`device`.
		"""
		return self._fs_subtype_map.get(ifmt(self.system.st_mode))

	@property
	def created(self):
		"""
		# Time of creation; UTC. Not available on all systems.
		"""
		return self._interpret_time(self.system.st_birthtime)

	@property
	def last_modified(self):
		"""
		# Time of last modification; UTC.
		"""
		return self._interpret_time(self.system.st_mtime)

	@property
	def last_accessed(self):
		"""
		# Time of last access; UTC.
		"""
		return self._interpret_time(self.system.st_atime)

	@property
	def meta_last_modified(self):
		"""
		# Time of last status change; UTC.
		"""
		return self._interpret_time(self.system.st_ctime)

	@property
	def owner(self):
		return self._read_user(self.system.st_uid)

	@property
	def group(self):
		return self._read_group(self.system.st_gid)

	@property
	def setuid(self):
		return (self.system.st_mode & stat.S_ISUID)

	@property
	def setgid(self):
		return (self.system.st_mode & stat.S_ISGID)

	@property
	def sticky(self):
		return (self.system.st_mode & stat.S_ISVTX)

	@property
	def executable(self, mask=stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH) -> bool:
		"""
		# Whether the data file is considered executable by anyone.

		# Extended attributes are not checked.
		"""
		return (self.system.st_mode & mask) != 0 and self.type == 'data'

	@property
	def searchable(self, mask=stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH) -> bool:
		"""
		# Whether the directory file is considered searchable by anyone.

		# Extended attributes are not checked.
		"""
		return (self.system.st_mode & mask) != 0 and self.type == 'directory'

@cachedcalls(32)
def path_string_cache(path):
	if path.context is not None:
		prefix = path_string_cache(path.context)
		segment = '/'.join(path.points)
		return '/'.join(x for x in (prefix, segment) if x)
	else:
		return '/'.join(path.points)

class Path(Selector[str]):
	"""
	# - &..route.abstract.Path
	# - &..route.abstract.File

	# Path implementation providing file system controls.
	# &.files.root is provided for convenience, and &.process.fs_pwd is
	# available for getting the working directory of the process.
	"""
	__slots__ = ('context', 'points',)
	context: Optional['Path']
	Violation = RequirementViolation

	_root_path = _path_separator = os.path.sep
	_fs_access = staticmethod(functools.partial(
		os.access,
		effective_ids=(os.access in os.supports_effective_ids)
	))
	_fs_access_map = {
		'r': os.R_OK,
		'w': os.W_OK,
		'x': os.X_OK,
		'/': 0,
		'!': 0,
	}

	def fs_require(self, properties:str='', *, type=None):
		# The cases involving '/', '!' and '?' properties are slightly odd,
		# but are intended to cover relatively common cases where the
		# use of an explicit type alone is insufficient.

		try:
			filetype = self.fs_type()
			if filetype == 'void':
				if type == 'void' or '!' in properties:
					# Nothing more to do; void case is accepted by caller.
					return self

				# Implied existence requirement.
				raise RequirementViolation(self, 'void', 'void', type, properties)
		except (NotADirectoryError, PermissionError) as fs_error:
			# Implied accessibility requirement.
			if '?' in properties:
				# Dismissed. Similar to accepting 'void' types.
				return self

			raise RequirementViolation(self, 'unknown', 'inaccessible', type, properties)
		else:
			assert filetype != 'void'

			if properties[:1] in type_codes:
				# Override iff properties starts with a type code, and type is None.
				if type is None:
					type = type_codes[properties[:1]]
				else:
					# Warn when both type and type code are designated?
					pass
				properties = properties[1:]

			if type is not None:
				# Specific type is required.
				if filetype != type:
					raise RequirementViolation(self, filetype, 'type', type, properties)
			else:
				# Check implied directory restriction.
				if filetype == 'directory' and '/' not in properties:
					assert type is None
					# Require a non-directory file by default unless '/' was in &properties.
					raise RequirementViolation(self, filetype, 'directory', type, properties)

			if properties:
				check = 0
				for x in properties:
					check |= self._fs_access_map[x]
				if not self._fs_access(self, check):
					raise RequirementViolation(self, filetype, 'prohibited', type, properties)

		return self

	@classmethod
	def from_path(Class, path:str, *, getcwd=os.getcwd):
		"""
		# Construct a &Path instance from the given absolute or relative path
		# provided for &string; if a relative path is specified, it will
		# be relative to the current working directory as identified by
		# &os.getcwd.

		# This is usually the most appropriate way to instantiate a &Path route
		# from user input. The exception being cases where the current working
		# directory is *not* the relevant context.
		"""

		if path and path[0] == '/':
			return Class.from_absolute(path)
		else:
			return Class.from_relative(Class.from_absolute(getcwd()), path)

	@classmethod
	def from_relative(Class, context, path:str, *, chain=itertools.chain):
		"""
		# Return a new Route pointing to the file referenced by &path;
		# where path is a path relative to the &context &Path instance.

		# This function does *not* refer to the current working directory
		# returned by &os.getcwd; if this is desired, &from_path is the
		# appropriate constructor to use.
		"""
		s = Class._path_separator

		points = Class._relative_resolution(chain(
			context.absolute,
			path.strip(s).split(s)
		))
		return Class(None, tuple(points))

	@classmethod
	def from_absolute(Class, path:str, tuple=tuple):
		return Class(None, tuple(x for x in path.split(Class._path_separator) if x))

	@classmethod
	def from_absolute_parts(Class, start:str, *paths:str):
		ps = Class._path_separator

		ini = start.split(ps)
		if ini and not ini[0]:
			ini = ini[1:]

		current = Class(None, tuple(ini))
		for p in paths:
			current = Class(current, tuple(p.split(ps)))

		return current

	@staticmethod
	def _partition_string(path:str) -> Iterable[Sequence[str]]:
		return (x.strip('/').split('/') for x in path.split("//"))

	@classmethod
	def from_partitioned_string(Class, path:str):
		"""
		# Construct an absolute path while interpreting consecutive separators
		# as distinct partitions.
		"""
		return Class.from_partitions(Class._partition_string(path))

	def __matmul__(self, path:str):
		parts = self._partition_string(path)
		if path[:1] == "/":
			return self.from_partitions(parts)
		else:
			return self // Segment.from_partitions(parts)

	@classmethod
	@contextlib.contextmanager
	def fs_tmpdir(Class, *, TemporaryDirectory=tempfile.mkdtemp):
		"""
		# Create a temporary directory at a new route using a context manager.

		# A &Path to the temporary directory is returned on entrance,
		# and that same path is destroyed on exit.

		# [ Engineering ]
		# The use of specific temporary files is avoided as they have inconsistent
		# behavior on some platforms.
		"""

		d = TemporaryDirectory()
		try:
			r = Class.from_absolute(d).delimit()
			yield r
		finally:
			assert str(r) == d
			try:
				r.fs_void()
			except NameError:
				os.rmdir(d)

	def __repr__(self):
		parts = ["/".join(p) for p in self.partitions() if p]
		if not parts:
			return "(file@'/')"
		parts[0] = "/" + parts[0]
		return "(file@%r)" %("//".join(parts),)

	def __str__(self):
		return self.fullpath

	@property
	def fullpath(self) -> str:
		"""
		# Returns the full filesystem path designated by the route.
		"""

		l = ['']
		if self.context is not None:
			l.append(path_string_cache(self.context))
		l.extend(self.points)

		return '/'.join(l) or '/'

	@property
	def bytespath(self, encoding=sys.getfilesystemencoding()) -> bytes:
		"""
		# Returns the full filesystem path designated by the route as a &bytes object
		# returned by encoding the &fullpath in &sys.getfilesystemencoding with
		# `'surrogateescape'` as the error mode.
		"""

		return self.fullpath.encode(encoding, "surrogateescape")

	def join(self, *parts:str) -> str:
		"""
		# Construct a string path using &self as the prefix and appending the path
		# fragments from &parts.

		# Segment instances should be given with an asterisk applied to the argument.
		"""

		if self.context is not None:
			ctxstr = self.context.fullpath
		else:
			ctxstr = ''

		subpath = self.points + parts
		if not subpath:
			return ctxstr or '/'

		return '/'.join((ctxstr, '/'.join(subpath)))

	@property
	def filename(self):
		"""
		# Filesystem specific alias for &identifier.
		"""
		return self.identifier

	@property
	def extension(self):
		"""
		# Return the last dot-extension of the filename.
		# &None if the filename has no `.` characters at all.
		"""

		i = self.identifier
		p = i.rfind('.')
		if p == -1:
			return None

		return i[p+1:]

	def suffix_filename(self, appended_suffix):
		"""
		# Modify the name of the file adding the given suffix.

		# Returns a new &Path Route.
		"""

		return self * (self.identifier + appended_suffix)
	suffix = suffix_filename

	def prefix_filename(self, prefix_string):
		"""
		# Modify the name of the file adding the given prefix.

		# Returns a new &Path Route.
		"""

		return self * (prefix_string + self.identifier)
	prefix = prefix_filename

	def __pos__(self, *, _chain=itertools.chain):
		context = self.context.absolute if self.context else []
		points = self.points

		# Resolve /./ and /../
		rpoints = self._relative_resolution(_chain(context, points))

		# Maintain context if possible.
		if context == rpoints[:len(context)]:
			ctx = self.context or root
			rpoints = rpoints[len(context):]
		else:
			ctx = root

		return self.__class__(ctx, tuple(rpoints))

	def fs_path_string(self) -> str:
		"""
		# Construct a normalized string representing the path to the file.

		# Relative resolution must still be explicitly performed, but empty
		# path entries delimiting partitions are eliminated.
		"""

		path = self
		path_seq = []

		# Invert points sequence.
		while path.context is not None:
			if any(path.points):
				path_seq.append(path.points)
			path = path.context
		else:
			if any(path.points):
				path_seq.append(path.points)

		# Join non-empty points in the path.
		return self._root_path + self._path_separator.join(
			self._path_separator.join(x for x in parts if x)
			for parts in reversed(path_seq)
		)
	__fspath__ = fs_path_string

	def fs_status(self, *, stat=os.stat) -> Status:
		return Status((stat(self.fullpath), self.identifier))

	def fs_type(self, *, ifmt=stat.S_IFMT, stat=os.stat, type_map=Status._fs_type_map) -> str:
		"""
		# The type of file the route points to. Transforms the result of an &os.stat
		# call into a string describing the (python/attribute)`st_mode` field.

		# [ Returns ]
		# - `'directory'`
		# - `'data'`
		# - `'pipe'`
		# - `'socket'`
		# - `'device'`
		# - `'void'`

		# If no file is present at the path or a broken link is present, `'void'` will be returned.
		"""

		try:
			s = stat(self.fullpath.rstrip('/') or '/')
		except FileNotFoundError:
			return 'void'

		return type_map.get(ifmt(s.st_mode), 'unknown')

	def fs_executable(self, *, get_stat=os.stat, mask=stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH) -> bool:
		"""
		# Whether the file at the route is considered to be an executable.
		"""

		mode = get_stat(self.fullpath).st_mode
		return (mode & mask) != 0

	def fs_follow_links(self, *, readlink=os.readlink, islink=os.path.islink) -> Iterable[Selector]:
		Class = self.__class__
		r = self

		while islink(str(r)):
			yield r

			target = readlink(str(r))

			if target[:1] == '/':
				r = Class.from_absolute(target)
			else:
				r = Class.from_relative(r.container, target)

		yield r

	def fs_iterfiles(self, /, type=None, *, scandir=os.scandir):
		"""
		# Generate &Path instances identifying the files held by the directory, &self.
		# By default, all file types are included, but if the &type parameter is given,
		# only files of that type are returned.

		# If &self is not a directory or cannot be searched, an empty iterator is returned.
		"""
		try:
			dl = scandir(self.fullpath)
		except OSError:
			# Error indifferent.
			# User must make explicit checks to interrogate permission/existence.
			return

		with dl as scan:
			if type is None:
				# No type constraint.
				for de in scan:
					yield self/de.name
			elif type == 'directory':
				# Avoids the stat call in the last branch.
				for de in scan:
					if de.is_dir():
						yield self/de.name
			else:
				# stat call needed (fs_type) to filter here.
				for de in scan:
					r = self/de.name
					if type == r.fs_type():
						yield r

	def fs_list(self, type='data', *, scandir=os.scandir):
		"""
		# Retrieve the list of files contained by the directory referred to by &self.
		# Returns a pair, the sequence of directories and the sequence of data files.

		# Sockets, pipes, devices, and other non-data files are not retained in the list.
		"""

		try:
			dl = scandir(self.fullpath)
		except OSError:
			# Error indifferent.
			# User must make explicit checks to interrogate permission/existence.
			return ([], [])

		dirs = []
		files = []

		with dl as scan:
			for de in scan:
				sub = self/de.name
				if de.is_dir():
					dirs.append(sub)
				else:
					typ = sub.fs_type()
					if sub.fs_type() == type:
						files.append(sub)

		return (dirs, files)

	def fs_index(self, type='data', *, Queue=collections.deque):
		"""
		# Generate pairs of directories associated with their files.

		# Sockets, pipes, devices, broken links, and other non-data files are not retained in the lists.
		"""

		dirs, files = self.delimit().fs_list(type=type)
		if not dirs and not files:
			return

		yield self, files
		cseq = Queue(dirs)

		while cseq:
			subdir = cseq.popleft()
			sd, sf = subdir.fs_list(type=type)

			yield subdir, sf

			# continue with subdirectories
			cseq.extend(sd)

	def fs_snapshot(self, /,
			process=(lambda x, y: y[0] == 'exception'),
			depth:Optional[int]=8,
			limit:Optional[int]=2048, *,
			ifmt=stat.S_IFMT, Queue=collections.deque, scandir=os.scandir,
			lstat=os.lstat,
		):
		if depth == 0 or limit == 0:
			# Allows presumption >= 1 or None.
			return []

		ftype = Status._fs_type_map.get

		cdepth = 0
		ncount = 0
		nelements = 0

		Element: TypeAlias = tuple[str, list[object], dict]
		elements:list[Element] = []
		cseq = Queue()
		getnext = cseq.popleft

		cseq.append((self.delimit(), elements, self.fullpath))

		count = len(cseq)
		while cseq:
			subdir, dirlist, fp = getnext()
			count -= 1

			add = dirlist.append
			try:
				scan = scandir(fp)
			except OSError as err:
				add(('exception', [], {'status': None, 'error': err}))
				continue

			with scan as scan:
				for de in scan:
					file = subdir/de.name

					try:
						st = de.stat()
						typ = ftype(ifmt(st.st_mode), 'unknown')
						attrs = {'status': st, 'identifier': de.name}
					except FileNotFoundError:
						try:
							st = lstat(subdir.join(de.name))
						except FileNotFoundError:
							# Probably concurrent delete in this case.
							continue

						typ = 'void'
						attrs = {'status': st, 'identifier': de.name}
					except Exception as err:
						typ = 'exception'
						attrs = {'status': st, 'identifier': de.name, 'error': err}

					record:Element = (typ, [], attrs)

					if process(file, record):
						continue
					add(record)

					nelements += 1
					if limit is not None and nelements >= limit:
						return elements

					if de.is_dir():
						cseq.append((file, record[1], file.fullpath))
						ncount += 1 # avoid len() call on deque

			if count <= 0 and ncount:
				cdepth += 1
				if depth is not None and cdepth >= depth:
					return elements
				count = ncount
				ncount = 0

		return elements

	def fs_since(self, since:int,
			traversed=None,
		) -> Iterable[tuple[int, Selector]]:
		"""
		# Identify the set of files that have been modified
		# since the given point in time.

		# The resulting iterable does not include directories.

		# [ Parameters ]

		# /since/
			# The point in time after which files and directories will be identified
			# as being modified and returned inside the result set.
		"""

		# Traversed holds real absolute paths.
		if not traversed:
			traversed = set()
			traversed.add(os.path.realpath(str(self)))
		else:
			rpath = os.path.realpath(str(self))
			if rpath in traversed:
				return
			else:
				traversed.add(rpath)

		dirs, files = self.fs_list()

		for x in files:
			mt = x.fs_status().last_modified
			if mt.follows(since):
				yield (mt, x)

		for x in dirs:
			yield from x.fs_since(since, traversed=traversed)

	def fs_real(self, exists=os.path.exists):
		for x in ~self:
			if exists(x.fullpath):
				return x

		return root

	def exists(self, exists=os.path.exists) -> bool:
		"""
		# Query the filesystem and return whether or not the file exists.

		# A Route to a symbolic link *will* return &False if the target does not exist.
		"""

		return exists(self.fullpath)

	def fs_modified(self, *, utime=os.utime):
		"""
		# Update the modification time of the file identified by &self.
		"""
		return utime(self.fullpath)

	def fs_size(self, *, stat=os.stat) -> int:
		"""
		# Return the size of the file as depicted by &os.stat.
		"""
		return stat(self.fullpath, follow_symlinks=True).st_size

	def get_last_modified(self) -> int:
		"""
		# Return the modification time of the file.
		"""

		return self.fs_status().last_modified

	def set_last_modified(self, time, utime=os.utime):
		"""
		# Set the modification time of the file identified by the &Route.
		"""

		return utime(self.__str__(), (-1, time.select('unix')/1000))

	def get_text_content(self, encoding:str='utf-8') -> str:
		"""
		# Retrieve the entire contents of the file as a &str.
		"""
		with self.fs_open('rt', encoding=encoding) as f:
			return f.read()

	def set_text_content(self, string:str, encoding:str='utf-8') -> None:
		"""
		# Modify the regular file identified by &self to contain the given &string.
		"""
		with self.fs_open('w', encoding=encoding) as f:
			f.write(string)

	def meta(self):
		"""
		# Return file specific meta data.

		# ! WARNING:
			# Preliminary API.
		"""

		st = self.fs_status()
		return (st.created, st.last_modified, st.st_size)

	def fs_void(self, *, rmtree=shutil.rmtree, remove=os.remove):
		fp = self.fullpath

		try:
			typ = self.fs_type(stat=os.lstat)
		except FileNotFoundError:
			# Work complete.
			return

		if typ == 'directory':
			return rmtree(fp)
		else:
			# typ is 'void' for broken links.
			try:
				return remove(fp)
			except FileNotFoundError:
				return
		return self

	def fs_replace(self, replacement, *, copytree=shutil.copytree, copyfile=shutil.copy):
		src = replacement.fullpath
		dst = self.fullpath
		self.fs_void() #* Removal for replacement.

		if replacement.fs_type() == 'directory':
			copytree(src, dst, symlinks=True, copy_function=copyfile)
		else:
			copyfile(src, dst)
		return self

	def fs_linear(self, *, scandir=os.scandir):
		position = self
		path = []
		while True:
			with scandir(position) as scan:
				try:
					first = next(scan)
				except StopIteration:
					# Empty directory, end of linear tree.
					pass
				else:
					# Check for second file.
					try:
						second = next(scan)
					except StopIteration:
						# Single Entry
						if first.is_dir():
							# Continuation.
							path.append(first.name)
							position /= first.name
							continue
						else:
							# Only one non-directory file.
							pass
				# End of linear tree.
				break
		return self + path

	def fs_reduce(self, discarded, *, scandir=os.scandir, move=os.rename, rmdir=os.rmdir):
		origin = discarded
		with scandir(origin) as scan:
			for de in scan:
				move(origin/de.name, self/de.name)

		delta = discarded.segment(self)
		for i in range(len(delta)):
			rmdir(origin ** i)

		return self

	def fs_link_relative(self, path, *, link=os.symlink):
		relcount, segment = self.correlate(path)
		target = '../' * (relcount - 1)
		target += '/'.join(segment)

		try:
			link(target, self.fullpath)
		except FileExistsError:
			self.fs_void()
			if self.fs_type() != 'void':
				raise

			link(target, self.fullpath)
		return self

	def fs_link_absolute(self, path, *, link=os.symlink):
		target = path.fullpath

		try:
			link(target, self.fullpath)
		except FileExistsError:
			self.fs_void()
			if self.fs_type() != 'void':
				raise

			link(target, self.fullpath)
		return self

	def fs_init(self, data:Optional[bytes]=None, *, mkdir=os.mkdir, exists=os.path.exists):
		"""
		# Create and initialize a data file at the route using the given &data.

		# If &data is &None, no write operation will occur for pre-existing files.
		# If &data is not &None, the bytes will be written regardless.

		# Returns the route instance, &self.
		# Leading directories will be created as needed.
		"""

		fp = self.fullpath
		if exists(fp):
			if data is not None:
				self.fs_store(data) #* Re-initialize data file.
			return self

		routes = []
		for p in ~self.container:
			if p.fs_type() != 'void':
				break
			routes.append(p)

		# Create leading directories.
		for x in reversed(routes):
			mkdir(x.fullpath)

		with self.fs_open('xb') as f: #* Save ACL errors, concurrent op created file
			f.write(data or b'')

		return self

	def fs_alloc(self, *, mkdir=os.mkdir):
		routes = []
		for p in ~(self ** 1):
			if p.fs_type() != 'void':
				break
			routes.append(p)

		# Create leading directories.
		for x in reversed(routes):
			mkdir(x.fullpath)

		return self

	def fs_mkdir(self, *, mkdir=os.mkdir, exists=os.path.exists):
		fp = self.fullpath
		if exists(fp):
			return self

		routes = []
		for p in ~self.container:
			if p.fs_type() != 'void':
				break
			routes.append(p)

		# Create leading directories.
		for x in reversed(routes):
			mkdir(x.fullpath)

		mkdir(fp)
		return self

	@contextlib.contextmanager
	def fs_open(self, *args, **kw):
		"""
		# Open the file pointed to by the route.

		# If the file doesn't exist, create it; if the directories
		# leading up to the file don't exist, create the directories too.
		"""

		f = open(self.fullpath, *args, **kw)
		try:
			f.__enter__()
			yield f
		except BaseException as err:
			if not f.__exit__(err.__class__, err, err.__traceback__):
				raise
		else:
			f.__exit__(None, None, None)

	def fs_load(self, *, mode='rb') -> bytes:
		try:
			with self.fs_open(mode) as f:
				return f.read()
		except FileNotFoundError:
			return b''

	def fs_store(self, data:bytes, *, mode='wb'):
		with self.fs_open(mode) as f:
			f.write(data)
			return self

root = Path(None, ())
null = root/'dev'/'null'
empty = (root/'var'/'empty').delimit()
