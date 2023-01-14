"""
# System teletype interfaces.
"""

def cells(text:str) -> int:
	"""
	# Calculate the number of character matrix cells needed to display the given &text string.
	"""

class Device(object):
	"""
	# System teletype device abstraction.
	"""

	def __init__(self, fd):
		pass

	@property
	def kport(self) -> int:
		"""
		# The file descriptor providing read and write operations to the device.
		"""

	def fileno(self) -> int:
		"""
		# The opened file descriptor.
		"""

	@classmethod
	def open(Class, path="/dev/tty") -> "Device":
		"""
		# Create a device instance by opening the given path.
		# Opens the device with reading and writing.
		"""

	def get_path(self) -> str:
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
