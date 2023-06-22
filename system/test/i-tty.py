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


def test_cells_chinese_sample(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells
	test/cells("天") == len("天")*2
	test/cells("天天") == len("天")*2*2
	test/cells("a天天") == 1 + len("天")*2*2
	test/cells("a天天a") == 2 + len("天")*2*2
	test/cells("谢谢你的春天") == len("谢谢你的春天")*2

	# ZWJ presumes valid sequence, max cell usage of participating codepoints.
	test/cells("天\u200D天") == 2
	# The max size is chosen when a sequence is seen.
	test/cells("天\u200Da") == 2
	test/cells("a\u200D天") == 2

def test_cells_ctlchars(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells

	test/cells("\x00\x01") == 0 # ctlen == 0
	test/cells("\x00\x01", 1) == 2
	test/cells("\x00\x01", 2) == 4
	test/cells("\x02\x01 春", 1) == 5
	test/cells("\x02\x01 春\x00", 1) == 6

def test_cells_combining(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells
	"""
	cells = module.cells

	test/cells("\u0300") == 0
	test/cells("\u0300\u0305") == 0

	test/cells("a\u0350scii") == len("ascii")
	test/cells("a\u0350 z\u0350") == 3

def test_cells_vs(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells

	# Variant Selectors.
	"""
	cells = module.cells

	test/cells("\ufe0f") == 0
	test/cells("#\ufe0f") == 2
	test/cells("A#\ufe0f") == 3
	test/cells("\ufe0e") == 0

def test_cells_sequences(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells

	# ZWJ sequences.
	"""
	cells = module.cells

	test/cells("a\u200Db") == 1
	test/cells("a\u200Dbc") == 2
	test/cells("za\u200Dbc") == 3

	# Early termination.
	test/cells("a\u200Db\u200Cc") == 2
	test/cells("a\u200D\u200Cbc") == 3

def test_cells_zerowidths(test):
	"""
	# - &.extensions.tty/module.c#cells
	# - &module.cells

	# Zero width cases.
	"""
	cells = module.cells

	zeros = [
		"\u2060",
		"\u200B",
		"\uFEFF", # BOM/Deprecated since Unicode 3.2.
	]
	for x in zeros:
		test/cells(x) == 0
		test/cells('a'+x+'b') == 2
		test/cells('a'+x) == 1
		test/cells(x+'b') == 1
