"""
# System teletype interfaces.
"""

def fs_device() -> str:
	"""
	# Attempt to identify the teletype device file associated with the process
	# using the standard I/O file descriptors.

	# [ Returns ]
	# The path to the device file.

	# [ Exceptions ]
	# /OSError/
		# Raised when standard input, output, and error are not associated with a
		# teletype device.
	"""

def cells(text:str) -> int:
	"""
	# Calculate the number of character matrix cells needed to display the given &text string.

	# [ Parameters ]
	# /text/
		# The characters being analyzed.

	# [ Returns ]
	# Number of horizontal cells needed to display the text.
	"""

class Device(object):
	"""
	# System teletype device abstraction.
	"""

	@classmethod
	def open(Class, path="/dev/tty") -> "Device":
		"""
		# Create a device instance by opening the given path.
		# Opens the device with reading and writing.

		# [ Parameters ]
		# /path/
			# The path to the (teletype) device file to open.
		"""

	def __init__(self, fd:int):
		"""
		# Initialize the instance with an already opened teletype device file.
		"""

	@property
	def kport(self) -> int:
		"""
		# The file descriptor providing read and write operations to the device.
		"""

	def fileno(self) -> int:
		"""
		# The opened file descriptor.
		"""

	def fs_path(self) -> str:
		"""
		# Get the filesystem path to the device.
		"""

	def set_controlling_process(self, pgid:int):
		"""
		# Update the controlling process group.
		"""

	def get_controlling_process(self) -> int:
		"""
		# Get the controlling process group.
		"""

	def get_window_dimensions(self) -> tuple[int, int]:
		"""
		# Get the number of horizontal and vertical cells that the terminal is displaying.
		"""

	def record(self):
		"""
		# Store attribute retrieved using tcgetattr in the object.
		"""

	def restore(self):
		"""
		# Restore attribute using tcsetattr previously saved with &record.
		"""

	def send_break(self, duration=0):
		"""
		# Send a break using tcsendbreak.
		"""

	def drain(self):
		"""
		# Drain output on device using tcdrain.
		"""

	def set_message_limits(self, vmin, vtime):
		"""
		# Update the VMIN and VTIME attributes.
		"""

	def set_raw(self):
		"""
		# Adjust the terminal flags to perform in raw mode.
		"""

	def set_cbreak(self):
		"""
		# Adjust the terminal flags to perform in cbreak mode.
		"""

	def set_cooked(self):
		"""
		# Adjust the terminal flags to perform in sane mode.
		"""
