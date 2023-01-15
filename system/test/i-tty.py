import sys
from .. import tty as module

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
		from .. import files
		test.isinstance(p, str)
		test/(files.root@p).fs_type() == 'device'

def test_cells(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells

	# ascii fast path
	test/cells("") == 0
	test/cells("ascii") == len("ascii")

	# combining characters should have no width
	test/cells("a\u0350scii") == len("ascii")
	test/cells("a\u0350 z\u0350") == 3

def test_cells_chinese_sample(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells
	test/cells("谢谢你的春天") == len("谢谢你的春天")*2

def test_cells_ctlchars(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells

	# fast path skip lets this through
	test/cells("\x00\x01") == 2

	# No fast path skip, so it generates an error.
	test/cells("\x02\x01 春") == -1
