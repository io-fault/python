import sys
from ...system import tty as module

def test_fs_device(test):
	"""
	# - &.extensions.tty/module.c#fs_device
	# - &module.fs_device
	"""
	# No way to validate this that isn't fairly redundant.
	try:
		p = module.fs_device()
	except OSError:
		# If there's no tty on stdio, this is success.
		pass
	else:
		from ...system import files
		test.isinstance(p, str)
		test/(files.root@p).fs_type() == 'device'
