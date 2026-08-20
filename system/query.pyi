"""
# High-level system inquiries for user information and environment derived paths.

# All information is retrieved from the system when invoked.
"""
from typing import Protocol
from collections.abc import Iterable
from . import files

def hostname() -> str:
	"""
	# Retrieve the hostname of the machine.
	"""

def executable_paths() -> Iterable[files.Path]:
	"""
	# Retrieve the directory paths used to find executables.

	# The (system/environ)`PATH` variable as separate &files.Path objects.
	"""

def executables(exename:str) -> Iterable[files.Path]:
	"""
	# Find executables in (system/environ)`PATH`.

	# Iterate over the directories listed in `PATH` and yield paths
	# containing &exename that are executable.

	# No caching is directly leveraged.
	"""

def executable(exename:str) -> files.Path:
	"""
	# Return the path to the first executable found by &executables.
	# &None when no executable could be found with that name.

	# No caching is directly leveraged.
	"""

def username() -> str:
	"""
	# Retrieve the user's name that owns the process. (real user)

	# If (system/environ)`USER` is set, return it.
	"""

def home() -> files.Path:
	"""
	# Retrieve the user's home directory.

	# If (system/environ)`HOME` is set, return it.
	"""

def user(field=None) -> int|str|files.Path:
	"""
	# Retrieve a field from the user's profile. If the requested &field is not
	# defined by the system or an empty string is returned by the system, &None is returned.

	# [ Parameters ]
	# /field/
		# /`'identifier'`/
			# Get the cached user's identifier as an integer. (default)
		# /`'name'`/
			# Get the cached user's name, ignoring (system/environ)`USER`
		# /`'title'`/
			# Get the cached user's title. (pw_gecos)
		# /`'role'`/
			# Get the cached user's role. (pw_class)
		# /`'shell'`/
			# Get the cached user's shell path.
		# /`'home'`/
			# Get the cached user's home directory, ignoring (system/environ)`HOME`.
	"""

def clock_ticks() -> int:
	"""
	# Retrieve the clock ticks necessary for calculating processing usage from
	# the POSIX (system/manual)`sysconf` call with (id)`SC_CLK_TCK`.
	"""

class ProcessMetrics(Protocol):
	"""
	# Mutable collection of process resource usage measurements.
	"""

	@classmethod
	def from_parts(Class,
			process_count:int=0, thread_count:int=0,
			zombie_count:int=0, suspended_count:int=0, locked_count:int=0,

			maximum_elapsed_time:float=0.0,
			total_cumulative_time:float=0.0,
			total_user_time:float=0.0,
			total_system_time:float=0.0,

			average_memory:float=0.0,
		):
		"""
		# Construct a new instance from the given keywords.
		"""

	def __add__(self, operand):
		"""
		# Combine the fields of the two measurements.
		# Counts are added, exceeded maximums are overwritten, and averages are
		# are recalculated with respect to the &process_count.
		"""

	@property
	def process_count(self) -> int:
		"""
		# Number of processes using the resources.
		"""

	@property
	def thread_count(self) -> int:
		"""
		# Number of threads running in the processes.
		"""

	@property
	def zombie_count(self) -> int:
		"""
		# Number of processes waiting to be reaped.
		"""

	@property
	def suspended_count(self) -> int:
		"""
		# Number of processes in a suspended state.
		"""

	@property
	def locked_count(self) -> int:
		"""
		# Number of processes in a locked state.
		"""

	@property
	def maximum_elapsed_time(self) -> float:
		"""
		# The longest running process' duration.
		"""

	@property
	def total_cumulative_time(self) -> float:
		"""
		# The sum of the runtimes of all the processes.

		# Often unavailable.
		"""

	@property
	def total_user_time(self) -> float:
		"""
		# User CPU time of the processes.
		"""

	@property
	def total_system_time(self) -> float:
		"""
		# System CPU time of the processes.
		"""

	@property
	def maximum_memory(self) -> float:
		"""
		# The peak memory usage of a single process.
		"""

	@property
	def average_memory(self) -> float:
		"""
		# The, current, average memory usage of the processes.
		"""

	@property
	def average_maximum_memory(self) -> float:
		"""
		# The average maximum memory usage of the processes.
		"""

def process_usage_scan(pid:int, limit:int=0) -> ProcessMetrics:
	"""
	# Gather resource usage information regarding the process tree identified
	# by &pid. When &pid is negative, either the process group or the control
	# group will be scanned depending on the platform. &limit restricts the
	# total number of process records to include in the aggregate.
	"""

def process_executable_path(pid:int) -> str:
	"""
	# Identify the executable currently associated with the process identified by &pid.
	"""
