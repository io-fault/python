"""
# Analyze &.delta
"""

from ...syntax import delta as module

def test_Update(test):
	r = module.Update(0, "", "", 0)
	test/r.element == 0
	test/r.position == 0
	test/r.insertion == ""
	test/r.deletion == ""
	test/list(r.usage()) != []

def test_Lines(test):
	r = module.Lines(0, [], [])
	test/r.element == 0
	test/r.insertion == []
	test/r.deletion == []
	test/list(r.usage()) != []

def test_Cursor(test):
	r = module.Cursor(0, -1, -2, -3)
	test/r.element == 0
	test/r.lines == -1
	test/r.codepoint_offset == -2
	test/r.codepoints == -3
	test/list(r.usage()) != []

def test_Checkpoint(test):
	r = module.Checkpoint(7)
	test/r.when == 7
	test/list(r.usage()) != []

def test_Log_init(test):
	l = module.Log()
	test/len(l.records) == 0
	test/l.count == 0
	test/l.committed == 0
	test/list(l.usage()) != []

def sample1():
	ds = []
	l = module.Log()
	l.write(module.Lines(0, ["init"], []))
	l.apply(ds)
	l.commit()
	return ds, l

def test_Log_insert(test):
	ds, l = sample1()
	test/ds == ["init"]

def test_Log_undo(test):
	ds, l = sample1()
	for d in l.undo(1):
		d.apply(ds)
	test/ds == []

def test_Log_redo(test):
	ds, l = sample1()
	l.write(module.Lines(0, ["replace"], []))
	l.write(module.Lines(2, ["suffix"], []))
	l.apply(ds)
	l.commit()
	for d in l.undo(1):
		d.apply(ds)
	for d in l.redo(1):
		d.apply(ds)
	test/ds == ["replace", "init", "suffix"]

def test_Log_truncate(test):
	"""
	# - &module.Log.truncate

	# Validate negative interpretations, uncommitted retention, and full truncation.
	"""

	ds, l = sample1()
	test/l.count == 1
	test/l.committed == 1
	l.truncate()
	test/l.count == 0
	test/l.committed == 0

	# Ignore uncommitted
	l.write(module.Lines(1, ["uncommitted"], []))
	test/ds == ["init"]
	test/l.count == 1
	test/l.committed == 0
	l.truncate()
	test/l.count == 1
	test/l.committed == 0
	# And again with negative offset.
	l.truncate(-2)
	test/l.count == 1
	test/l.committed == 0

	# Apply and test truncates.
	l.apply(ds)
	l.commit()
	test/ds[-1] == "uncommitted"
	test/l.count == 1
	l.truncate(-1)
	test/l.count == 1
	l.truncate(1)
	test/l.count == 0

	for i in range(24):
		l.write(module.Lines(0, [str(i)], []))
	test/l.count == 24
	test/l.committed == 0
	# Refuse to truncate uncommitted.
	l.truncate()
	l.truncate(12)
	l.truncate(24)
	test/l.count == 24
	test/l.committed == 0
	l.apply(ds)
	l.commit()
	test/l.count == l.committed

	l.truncate(6)
	test/l.count == (24 - 6)
	test/l.count == l.committed

	# Deleting to the 10'th record.
	l.truncate(-8)
	test/l.count == ((24 - 6) - 10)
	test/l.count == l.committed

def test_Log_checkpoint(test):
	ds, l = sample1()
	l.checkpoint()
	l.write(module.Lines(1, ["after-cp"], []))
	l.apply(ds)
	l.commit()
	test/ds[1] == "after-cp"
	for d in l.undo(1):
		d.apply(ds)
	test.isinstance(l.future[-1], module.Checkpoint)
	test/ds == ["init"]

def test_Log_update(test):
	ds, l = sample1()
	l.write(module.Update(0, "--between--", "", 2))
	l.apply(ds)
	test/ds == ["in--between--it"]
	l.commit()
	test/ds == ["in--between--it"]

def test_Log_collapse_inserts(test):
	ds, l = sample1()
	l.write(module.Update(0, "1", "", 4))
	l.apply(ds)
	l.commit()

	# Combine with the empty update.
	l.write(module.Update(0, "append", "", 5))
	l.apply(ds)
	l.collapse()
	test/ds == ["init1append"]
	test/l.committed == l.count
	test/len(l.records) == 2

	# Check that the combined record gives the same result.
	for d in l.undo(1):
		d.apply(ds)
	test/ds == []
	for d in l.redo(1):
		d.apply(ds)
	test/ds == ["init1append"]

def test_Log_collapse_deletes(test):
	"""
	# - &module.Update.combine
	# - &module.Log.collapse

	# Validate that deletes following inserts can be combined.
	"""

	ds, l = sample1()
	l.write(module.Update(0, "append", "", 4))
	l.apply(ds)
	l.commit()

	# Combine with the empty update.
	l.write(module.Update(0, "", "end", 4+3))
	l.apply(ds).collapse().commit()
	test/ds == ["initapp"]
	test/len(l.records) == 2 # Eliminated one.

	# Check that the combined record gives the same result.
	for d in l.undo(1):
		d.apply(ds)
	test/ds == []
	for d in l.redo(1):
		d.apply(ds)
	test/ds == ["initapp"]

def test_Log_collapsed_since(test):
	"""
	# - &module.Log.collapse
	# - &module.Log.since
	"""
	ds, l = sample1()

	# Add "append" to sample1's "init".
	before = l.snapshot()
	l.write(module.Update(0, "append", "", 4))
	l.apply(ds).commit()
	after = l.snapshot()

	# Collapse append.
	l.write(module.Update(0, "+tail-1", "", 4+len("append")))
	l.apply(ds).collapse().commit()
	test/ds == ["initappend+tail-1"]
	test/l.committed == l.count

	brecords = list(l.since(before))
	arecords = list(l.since(after))
	test/len(brecords) == 1
	test/len(arecords) == 1
