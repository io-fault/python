"""
# High-level system inquiries for user information and environment derived paths.

# All information is retrieved from the system when invoked.
"""
from typing import Protocol
from . import files

def paths(environment:str='PATH') -> files.Path:
	"""
	# Select paths present in the (system/environ)`PATH` variable.
	"""

def executables(exename:str, environment:str='PATH') -> files.Path:
	"""
	# Select executable paths from the environment, (system/environ)`PATH`.

	# Iterate over the directories listed in `PATH` and yield paths that exist
	# when the given &exename is extended on the directory.

	# The produced &.files.Path instances may refer to files of any type.
	# Paths referring to broken links will not be included.
	"""

def home(environment:str='HOME') -> files.Path:
	"""
	# Retrieve the user's home directory from the environment, (system/environ)`HOME`.

	# If the environment variable is not set, the (id)`pw_dir` field will be retrieved
	# using &pwd.
	"""

def username() -> str:
	"""
	# Retrieve the user's name.
	"""

def usertitle() -> str:
	"""
	# Retrieve the user's title; the long name associated with the user.

	# The (id)`pw_gecos` field is retrieved using &pwd without modification.
	# If the system has no such concept or it cannot be resolved, &None is returned.
	"""

def shell() -> files.Path:
	"""
	# Retrieve the path to the user's login shell.

	# If the system has no such concept or it cannot be resolved, &None is returned.
	"""

def hostname() -> str:
	"""
	# Retrieve the hostname using the POSIX (system/manual)`gethostname(2)` call.
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
