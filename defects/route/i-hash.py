from ...route import hash as module
from ...system import files

def test_Index_structure(test):
	s1 = [
		b'entry\n',
		b'\tkey1\n',
		b'\tcontinue\n',
	]

	test/list(module.Index.structure(s1)) == [(b'key1\ncontinue', b'entry')]

	s1 = [
		b'1\n',
		b'entry\n',
		b'\tkey1\n',
		b'\tcontinue\n',

		b'entry2\n',
		b'\tkey!\n',
	]

	istruct = [(b'', b'1'), (b'key1\ncontinue', b'entry'), (b'key!', b'entry2')]
	test/list(module.Index.structure(s1)) == istruct

def test_Index(test):
	idx = module.Index()

	# Entry identifier increment.
	entries = idx.allocate((b'key1', b'key2'), str)
	test/entries == ["1", "2"]

	# Check serialization
	l = list(idx.sequence())
	possibilities = [
		[b'2\n', b'1\n\tkey1\n', b'2\n\tkey2\n'],
		[b'2\n', b'2\n\tkey2\n', b'1\n\tkey1\n'],
	]
	test/possibilities << l

	lidx = module.Index()
	lidx.load([x+b'\n' for x in b''.join(l).split(b'\n')])
	test/lidx.counter == 2
	test/lidx._map << b'key1'
	test/lidx._map << b'key2'

	# Check for filename customization along with continuation after load.
	entries = idx.allocate((b'key3',), lambda x: 'F.' + str(x) + '.exe')
	test/entries == ['F.3.exe']

def test_Segmentation(test):
	h = module.Segmentation.from_identity()
	path = h(b'http://foo.com/some/resource.tar.gz')

	test/sum(map(len, path)) == h.length
	test/len(path) == h.depth

def test_Directory_operations(test):
	"""
	# - &module.Directory.__init__
	# - &module.Directory.allocate
	# - &module.Directory.available
	# - &module.Directory.release
	"""
	tmp = test.exits.enter_context(files.Path.fs_tmpdir())
	htd = (tmp/'h').fs_mkdir()

	# Initialize
	d = module.Directory(module.Segmentation.from_identity(), htd)
	test/d.available(b'test') == True

	# Allocate
	r = d.allocate(b'test')
	test/d.available(b'test') == False
	test/r.fs_type() == 'directory'

	# Release
	test/d.release(b'test') == r
	test/d.available(b'test') == True
	test/r.fs_type() == 'void'

	# No entry.
	test/d.release(b'none') == None

def test_Directory_updates(test):
	"""
	# - &module.Index.load
	# - &module.Index.sequence
	"""
	tmp = test.exits.enter_context(files.Path.fs_tmpdir())
	htd = (tmp/'h').fs_mkdir()

	d = module.Directory(module.Segmentation.from_identity(), htd)
	r1 = d.allocate(b'test')
	test/r1.fs_type() == 'directory'

	d2 = module.Directory(module.Segmentation.from_identity(), htd)
	r2 = d.allocate(b'test')
	test/r2 == r1

def test_Directory_items(test):
	"""
	# - &module.Directory.items
	"""
	tmp = test.exits.enter_context(files.Path.fs_tmpdir())
	htd = (tmp/'h').fs_mkdir()

	d = module.Directory(module.Segmentation.from_identity(), htd)
	t1 = d.allocate(b'test-1')
	test/set(d.items()) == {(b'test-1', t1)}
	t2 = d.allocate(b'test-2')
	test/set(d.items()) == {(b'test-1', t1), (b'test-2', t2)}
