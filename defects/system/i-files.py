"""
# Check the implementation of filesystem routes.
"""
import sys
import functools
import os.path

from ...system import files as module
from ...time.system import utc as time

@functools.singledispatch
def d_setup(x:bytes, path:module.Path):
	path.fs_init(x)

@d_setup.register
def _(x:dict, path:module.Path):
	for k, v in x.items():
		d_setup(v, path/k)

def test_constants(test):
	"""
	# Check for &.files.root presence and sanity.
	"""

	names = ['root', 'null', 'empty']

	for n in names:
		test/hasattr(module, n) == True
		cp = getattr(module, n)
		test.isinstance(cp, module.Path)

	test/str(module.root) == "/"
	test/str(module.null) == "/dev/null"
	test/str(module.empty) == "/var/empty"

	for i in range(8):
		test/(module.root ** i) == module.root
	test/(module.empty/'context-test').context == module.empty

def test_Path(test):
	dir = os.path.dirname(os.path.realpath(__file__))
	r = module.Path.from_absolute(os.path.realpath(__file__))
	test/r.fullpath == os.path.realpath(__file__)

	rd = r.container
	test/rd.fullpath == dir

	test/(rd/'foo').fullpath == os.path.join(dir, 'foo')
	test/module.Path.from_absolute('/foo/bar.tar.gz').extension == 'gz'

def test_Path_filename(test):
	p = module.Path.from_absolute('/no/such/path')

	f = p/'data.tar.xz'
	test/p.filename == 'path'
	test/f.filename == 'data.tar.xz'
	test/f.extension == 'xz'

def test_Path_repr(test):
	end = module.Path.from_absolute('/test')
	test/repr(end).__contains__('/test') == True

	nx = module.Path.from_absolute_parts('/usr/lib', 'python3.5m/site-packages', 'somemod.py')
	rstr = repr(nx)
	test/rstr.__contains__('/somemod.py') == True
	test/rstr.__contains__('/usr/') == True

def test_Path_string_cache(test):
	r = module.Path.from_absolute('/')

	p1 = module.Path.from_absolute('/test/string/path')
	test/module.path_string_cache(p1) == 'test/string/path'

	p2 = r@"test//string//path"
	test/module.path_string_cache(p2) == 'test/string/path'
	test/module.path_string_cache(p2 ** 1) == 'test/string'
	test/module.path_string_cache(p2 ** 2) == 'test'
	test/module.path_string_cache(p2 ** 3) == ''

def test_Path_from_partitioned_string(test):
	p = module.Path.from_partitioned_string("/root//prefix/stem//local/target")
	parts = p.partitions()
	test/parts == [
		('root',),
		('prefix', 'stem',),
		('local', 'target',),
	]

def test_Path_bytespath(test):
	p = module.Path.from_absolute('/test/path')
	test/p.bytespath == b'/test/path'

def test_Path_temporary(test):
	path = None
	with module.Path.fs_tmpdir() as t:
		path = t.fullpath
		test/os.path.exists(path) == True
		test/t.fs_type() == 'directory'

	# temporary context over, should not exist.
	test/os.path.exists(path) == False

def test_Path_list(test):
	"""
	# - &module.Path.fs_list
	"""

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	test/t.fs_list() == ([],[])
	expect = ([t/str(i) for i in range(24, 32)], [t/str(i) for i in range(16)])

	for i in range(16):
		(t/str(i)).fs_init()

	dl = t.fs_list()
	for l in dl:
		l.sort(key=(lambda x: int(x.identifier)))
	test/dl[1] == expect[1]
	test/dl[0] == []

	for i in range(24, 32):
		(t/str(i)).fs_mkdir()

	dl = t.fs_list()
	for l in dl:
		l.sort(key=(lambda x: int(x.identifier)))

	test/dl == expect

def test_Path_iterfiles(test):
	"""
	# - &module.Path.fs_iterfiles
	"""
	K = (lambda x: int(x.identifier))

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	test/list(t.fs_iterfiles()) == []

	expect_files = [t/str(i) for i in range(16)]
	expect_dirs = [t/str(i) for i in range(24, 32)]
	expect_both = expect_files + expect_dirs
	expect_files.sort(key=K)
	expect_dirs.sort(key=K)
	expect_both.sort(key=K)

	for i in range(16):
		(t/str(i)).fs_init()

	dl = list(t.fs_iterfiles())
	dl.sort(key=K)
	test/dl == expect_files

	for i in range(24, 32):
		(t/str(i)).fs_mkdir()

	dl = list(t.fs_iterfiles())
	dl.sort(key=K)
	test/dl == expect_files + expect_dirs

	dl = list(t.fs_iterfiles('directory'))
	dl.sort(key=K)
	test/dl == expect_dirs

	dl = list(t.fs_iterfiles('data'))
	dl.sort(key=K)
	test/dl == expect_files

	test/list(t.fs_iterfiles('socket')) == []
	test/list(t.fs_iterfiles('device')) == []
	test/list(t.fs_iterfiles('pipe')) == []

def test_Path_index(test):
	"""
	# - &module.Path.fs_index
	# - &module.Path.fs_list
	"""

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	f = t / 'file'
	f.fs_init()
	test/f.fs_list() == ([],[]) # OSError
	test/dict(f.fs_index()) == {}

	d = t / 'dir'
	s = d / 'subdir'
	l = s / 'file-in-subdir'
	l.fs_init()

	expect = {
		t: [f],
		d: [],
		s: [l],
	}
	queried = dict(t.fs_index())

	test/queried == expect

def test_Path_snapshot(test):
	"""
	# - &module.Path.fs_snapshot
	"""
	sk = (lambda x: x[2]['identifier'])

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	f = (t / 'file').fs_init()
	report = t.fs_snapshot()
	expect = [
		('data', [], {'status': os.stat(f.fullpath), 'identifier': f.identifier})
	]

	test/report == expect # single file entry

	d = (t / 'dirname').fs_mkdir()
	expect.append(
		('directory', [], {'status': os.stat(d.fullpath), 'identifier': d.identifier})
	)
	expect.sort(key=sk)
	report = t.fs_snapshot()
	report.sort(key=sk)
	test/report == expect # file and directory

def test_Path_real(test):
	"""
	# - &module.Path.fs_real
	"""
	t = test.exits.enter_context(module.Path.fs_tmpdir())
	f = t/'doesnotexist'

	r = f.fs_real()
	test/f.fs_real() != f
	test/r == t

	d = (t/'subdir').fs_mkdir()
	test/d.fs_real() == d

	i = d@"i1/i2/i3/i4/i5/i6/i7/i8/i9"
	test/i.fs_real() == d

def test_Path_replace(test):
	# Regular file replacement.
	t = test.exits.enter_context(module.Path.fs_tmpdir())
	src = t / 'srcfile'
	with src.fs_open('wb') as f:
		f.write(b'sources')

	dst = t / 'dstfile'
	with dst.fs_open('wb') as f:
		f.write(b'dest')

	dst.fs_replace(src)
	with dst.fs_open('rb') as f:
		test/f.read() == b'sources'

	src = t / 'srcdir'
	srcfile = src / 's' / 's'
	srcfile.fs_init()
	with srcfile.fs_open('wb') as f:
		f.write(b'subdir_sources')

	dst.fs_replace(src)
	test/(dst / 's').fs_type() != 'void'
	test/(dst / 's' / 's').fs_type() != 'void'
	dir = dst / 's'
	test/dir.fs_type() == 'directory'
	file = dir / 's'
	with file.fs_open('rb') as f:
		test/f.read() == b'subdir_sources'

def test_Path_init(test):
	"""
	# Test &module.Path.fs_init checking that the parent directories are
	# properly created regardless of the selected type.
	"""

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	f = t / 'parent-2' / 'filename'

	f2 = f.fs_init(b'content')
	test/f2 == f
	test/f.fs_type() == 'data'
	test/f.identifier == 'filename'

	test/f.fs_load() == b'content'
	test/f.fs_init(b'content-2').fs_load() == b'content-2'
	test/f.fs_init().fs_load() == b'content-2'

def test_Path_mkdir(test):
	"""
	# Test &module.Path.fs_mkdir checking that the parent directories are
	# properly created regardless of the selected type.
	"""

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	d = t / 'parent-2' / 'directory'

	d2 = d.fs_mkdir()
	test/d2 == d
	test/d.fs_type() == 'directory'
	test/d.identifier == 'directory'

	s = (d/'subdir').fs_mkdir()
	test/s.fs_type() == 'directory'
	test/s.identifier == 'subdir'

def test_Path_type_void(test):
	"""
	# - &module.Path.fs_type
	"""

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	l = t / 'deadlink.txt'
	d = t / 'directory'
	f = t / 'data-file.txt'
	d.fs_mkdir()
	f.fs_init(b'nothing')
	l.fs_link_relative(d/'no-such-target')

	v1 = d / 'subdirectory'
	test/v1.fs_type() == 'void'
	nosub = d@'fnf/no-such-file'
	test/nosub.fs_type() == 'void'

	v2 = f / 'erroneous-subfile'
	test/NotADirectoryError ^ v2.fs_type

	v3 = l
	test/v3.fs_type() == 'void'

def test_Path_extension(test):
	f = module.Path.from_path('test')
	test/f.extension == None

	f = module.Path.from_path('test.xyz')
	test/f.extension == 'xyz'

def test_Path_size(test):
	r = module.Path.from_path(__file__)

	d = r.container / 'test-size-info'

	f1 = d / 'one'
	f2 = d / 'two'
	f3 = d / 'three'
	f4 = d / 'four'
	test/f1.fs_size() == 1
	test/f2.fs_size() == 2
	test/f3.fs_size() == 3
	test/f4.fs_size() == 4

def test_Path_get_last_modified(test):
	"""
	# System check.
	"""
	import time

	d = test.exits.enter_context(module.Path.fs_tmpdir())
	r = d / 'last_modified_testfile'
	with r.fs_open('w') as f:
		f.write('data\n')

	test/r.fs_type() != 'void'

	mtime1 = r.get_last_modified()
	time.sleep(1.1)
	# sleep one whole second in case the filesystem's
	# precision is at the one second mark.

	with r.fs_open('a') as f:
		f.write('appended\n')

	mtime2 = r.get_last_modified()

	test/mtime2 > mtime1
	m = mtime2.__class__.Measure.of(second=1)
	test/mtime1.measure(mtime2) >= m

def test_Path_set_last_modified(test):
	"""
	# System check.
	"""

	d = test.exits.enter_context(module.Path.fs_tmpdir())
	r = d / 'last_modified_testfile'
	with r.fs_open('w') as f:
		f.write('data\n')

	test/r.fs_type() != 'void'
	original_time = r.get_last_modified()

	ttime = time().update('minute', -10, 'hour')

	r.set_last_modified(ttime)
	new_time = r.get_last_modified()

	test/new_time != original_time
	test/new_time.truncate('second') == ttime.truncate('second')

def test_Path_get_text_content(test):
	"""
	# Validate &module.Path.get_text_content.
	"""

	d = test.exits.enter_context(module.Path.fs_tmpdir())
	r = d / 'tf'
	with r.fs_open('w', encoding='utf-8') as f:
		f.write("data\n")
	test/r.fs_type() != 'void' # sanity
	test/r.get_text_content() == "data\n"

def test_Path_set_text_content(test):
	"""
	# Validate &module.Path.set_text_content.
	"""

	d = test.exits.enter_context(module.Path.fs_tmpdir())
	r = d / 'tf'
	test/r.set_text_content("data\n")
	with r.fs_open(encoding='utf-8') as f:
		test/f.read() == "data\n"

def test_Path_since(test):
	"""
	# &module.Path.fs_since
	"""

	root = test.exits.enter_context(module.Path.fs_tmpdir())
	f1 = root / 'file1'
	f2 = root / 'file2'
	f3 = root / 'file3'

	files = [f1, f2, f3]
	for x in files:
		x.fs_init()

	times = [x.get_last_modified() for x in files]
	times.sort(reverse=True)
	y = times[0]

	test/list(root.fs_since(time())) == []

	m = root.fs_since(time().rollback(minute=1))
	test/set(x[1] for x in m) == set(files)

def test_Path_construct(test):
	"""
	# Test the various classmethods that construct file instances.
	"""

	test/str(module.Path.from_absolute('/')) == '/'

	context = module.Path.from_absolute('/no/such/directory')

	test/str(module.Path.from_relative(context, 'file')) == '/no/such/directory/file'
	test/str(module.Path.from_relative(context, './file')) == '/no/such/directory/file'

	test/str(module.Path.from_relative(context, '../file')) == '/no/such/file'
	test/str(module.Path.from_relative(context, '../../file')) == '/no/file'

	# Same directory
	test/str(module.Path.from_relative(context, '../.././././file')) == '/no/file'

	# parent references that find the limit.
	test/str(module.Path.from_relative(context, '../../..')) == '/'
	test/str(module.Path.from_relative(context, '../../../..')) == '/'

	# Smoke test .from_path; two branches that use prior tested methods.
	test/str(module.Path.from_path('./file')) == os.getcwd() + '/file'
	test/str(module.Path.from_path('file')) == os.getcwd() + '/file'
	test/str(module.Path.from_path('/file')) == '/file'

def test_Path_relative_resolution(test):
	"""
	# - &module.Path.__pos__
	"""

	# Constrainted at root.
	outside = (module.root@"././..")
	test/str(outside) != str(module.root)
	test/str(+outside) == str(module.root)

	# Parent with superfluous trailing slash.
	leading = (module.root@"path/to/leading/./trimmed/../")
	test/leading != module.root@"path/to/leading"
	test/(+leading) == module.root@"path/to/leading"

	# Self references only.
	selves = (module.root@"path/././././")
	test/selves != module.root@"path"
	test/(+selves) == module.root@"path"

def test_Path_basename_manipulations(test):
	"""
	# - &module.Path.prefix_filename
	# - &module.Path.suffix_filename
	"""
	t = test.exits.enter_context(module.Path.fs_tmpdir())
	f = t/'doesnotexist'
	f_archive = f.suffix_filename('.tar.gz')
	test/f_archive.fullpath.endswith('.tar.gz') == True
	f_test_archive = f.prefix_filename('test_')
	test/f_test_archive.identifier.startswith('test_') == True

def test_Path_join(test):
	"""
	# - &module.Path.join
	"""
	test/module.root.join() == '/'
	test/module.root.join('file') == '/file'

	f = module.Path.from_absolute('/var/empty')

	test/f.join('datafile') == "/var/empty/datafile"
	test/f.join('subdir', 'datafile') == "/var/empty/subdir/datafile"
	test/f.join('subdir/datafile') == "/var/empty/subdir/datafile"

	test/f.join('super', 'subdir/datafile') == "/var/empty/super/subdir/datafile"

def test_Path_properties(test):
	# executable
	sysexe = module.Path.from_absolute(sys.executable)
	test/sysexe.fs_status().executable == True
	test/sysexe.fs_type() == 'data'

	module_path = module.Path.from_absolute(__file__)
	test/module_path.fs_status().executable == False
	test/module_path.fs_type() == 'data'

	moddir = module_path.container
	test/moddir.fs_type() == 'directory'

def test_Path_open(test):
	"""
	# - &module.File.fs_open
	"""
	d = test.exits.enter_context(module.Path.fs_tmpdir())

	r = d/'test'
	with r.fs_open('wb') as f:
		f.write(b'test-content')

	test/r.fs_load() == b'test-content'

	with r.fs_open('w', encoding='utf-8') as f:
		f.write('test-content-2')

	test/r.fs_load() == b'test-content-2'

	fnf = d/'no-such-file'
	try:
		with fnf.fs_open('r') as f:
			pass
	except Exception as err:
		test.isinstance(err, FileNotFoundError)

def test_Path_open_exception(test):
	"""
	# - &module.File.fs_open
	"""
	d = test.exits.enter_context(module.Path.fs_tmpdir())

	r = d/'test'
	try:
		with r.fs_open('rb') as f:
			pass
	except FileNotFoundError:
		pass
	else:
		test.fail("file not found not raised by context manager")

def test_Path_void(test):
	"""
	# - &module.Path.fs_void
	"""

	d = test.exits.enter_context(module.Path.fs_tmpdir())
	sd = d / 'subdir'
	sf = sd / 'subfile'
	sf.fs_init()

	with sf.fs_open('wb') as x:
		x.write(b'data')

	test/sd.fs_type() != 'void'
	test/sf.fs_type() != 'void'
	sf.fs_void()
	test/sf.fs_type() == 'void'
	sf.fs_init()
	test/sf.fs_type() != 'void'

	sd.fs_void()
	test/sd.fs_type() == 'void'
	test/sf.fs_type() == 'void'

def link_checks(test, create_link):
	t = test.exits.enter_context(module.Path.fs_tmpdir())

	target = t / 'file'
	target.fs_init(b'test file')

	# Relative Mode
	sym = t / 'symbolic'
	test/sym.fs_type() == 'void'

	create_link(sym, target)
	test/list(sym.fs_follow_links())[-1] == target

	test/sym.fs_type() != 'void'
	with sym.fs_open('rb') as f:
		test/f.read() == b'test file'
	target.fs_void()
	test/target.fs_type() == 'void'
	test/sym.fs_type() == 'void'
	test/list(sym.fs_follow_links())[-1] == target

	common = t / 'dir' / 'subdir'
	common.fs_mkdir()
	dst = common / 'from-1' / 'from-2' / 'file'
	src = common / 'to-1' / 'to-2' / 'to-3' / 'file'
	src.fs_init(b'source data')

	dst.fs_init()
	dst.fs_void()
	create_link(dst, src)
	test/list(dst.fs_follow_links())[-1] == src
	test/dst.fs_load() == b'source data'

def test_Path_relative_links(test):
	"""
	# &module.Path.fs_link_relative
	"""
	link_checks(test, module.Path.fs_link_relative)

def test_Path_absolute_links(test):
	"""
	# &module.Path.fs_link_absolute
	"""
	link_checks(test, module.Path.fs_link_absolute)

def test_Path_recursive_since(test):
	"""
	# &module.Path.fs_since with recursive directories.
	"""
	import itertools
	ago10mins = time().rollback(minute=10)
	thirty = time().rollback(minute=30)

	t = test.exits.enter_context(module.Path.fs_tmpdir())
	d = t / 'dir' / 'subdir'
	f = d / 'file'
	f.fs_init()

	for dd, files in t.fs_index():
		dd.set_last_modified(thirty)
		for x in files:
			x.set_last_modified(thirty)

	f.set_last_modified(ago10mins)

	# create recursion
	l = d / 'link'
	l.fs_link_relative(t / 'dir')
	test/list(t.fs_since(ago10mins.rollback(minute=10)))[0][1] == f

def test_Path_follow_links(test):
	"""
	# - &module.Path.fs_follow_links
	"""
	td = test.exits.enter_context(module.Path.fs_tmpdir())

	t = (td/'target.s')
	t.fs_init()

	l1 = (td/'link1')
	l1.fs_link_relative(t)

	l2 = (td/'link2')
	l2.fs_link_relative(l1)

	l3 = (td/'link3')
	l3.fs_link_relative(l2)

	test/list(map(str, l3.fs_follow_links())) == list(map(str, [l3, l2, l1, t]))
	test/list(map(str, l2.fs_follow_links())) == list(map(str, [l2, l1, t]))
	test/list(map(str, l1.fs_follow_links())) == list(map(str, [l1, t]))
	test/list(map(str, t.fs_follow_links())) == list(map(str, [t]))

def test_Path_io(test):
	"""
	# - &module.Path.fs_load
	# - &module.Path.fs_store
	"""
	td = test.exits.enter_context(module.Path.fs_tmpdir())

	f = td/'test-file'
	f.fs_init(b'')
	test/f.fs_type() == 'data'

	f.fs_store(b'bytes-data')
	test/f.fs_load() == b'bytes-data'
	with f.fs_open() as fp:
		test/fp.read() == "bytes-data"

	f.fs_store(b'overwritten')
	test/f.fs_load() == b'overwritten'
	with f.fs_open() as fp:
		test/fp.read() == "overwritten"

def test_Path_python_protocol(test):
	"""
	# - &module.Path.__fspath__
	"""
	t = test.exits.enter_context(module.Path.fs_tmpdir()) / 'data-file'
	t.fs_store(b'file-content')
	with open(t, 'rb') as f:
		test/b'file-content' == f.read()

def test_Path_snapshot_sanity(test):
	"""
	# - &module.Path.fs_snapshot
	"""

	td = test.exits.enter_context(module.Path.fs_tmpdir())
	d_setup({
		'subdir': {
			'name-1': b'-' * 256,
			'name-2': b'+' * 256,
		},
		'file-1': b'data1',
		'file-2': b'data2',
	}, td)

	elements = td.fs_snapshot()

	test/len(elements) == 3
	test/set(x[2]['identifier'] for x in elements) == {'subdir', 'file-1', 'file-2'}

	sub = [x for x in elements if x[2]['identifier'] == 'subdir'][0][1]
	test/set(x[2]['identifier'] for x in sub) == {'name-1', 'name-2'}
	test/sum(x[2]['status'].st_size for x in sub) == 512

def test_Path_snapshot_limit(test):
	"""
	# - &module.Path.fs_snapshot
	"""

	td = test.exits.enter_context(module.Path.fs_tmpdir())
	d_setup({
		'subdir': {
			'name-1': b'-' * 256,
			'name-2': b'+' * 256,
		},
		'file-1': b'data1',
		'file-2': b'data2',
	}, td)

	elements = td.fs_snapshot(limit=0)
	test/len(elements) == 0

	elements = td.fs_snapshot(limit=1)
	test/len(elements) == 1

	elements = td.fs_snapshot(limit=4)
	test/len(elements) == 3
	sub = [x for x in elements if x[2]['identifier'] == 'subdir'][0][1]
	test/len(sub) == 1

def test_Path_snapshot_depth(test):
	"""
	# - &module.Path.fs_snapshot
	"""

	td = test.exits.enter_context(module.Path.fs_tmpdir())
	d_setup({
		'subdir': {
			'name-1': b'-' * 256,
			'name-2': b'+' * 256,
		},
		'file-1': b'data1',
		'file-2': b'data2',
		'nesting': {
			'nesting': {
				'nesting': {
					'end-of-nest': b'data'
				},
			},
		},
	}, td)

	elements = td.fs_snapshot(depth=0)
	test/len(elements) == 0

	elements = td.fs_snapshot(depth=1)
	test/len(elements) == 4

	# Check for empty directories caused by the depth limit.
	sub = [x for x in elements if x[0] == 'directory']
	xcount = 0
	for x in elements:
		if x[0] == 'directory':
			test/len(x[1]) == 0
			xcount += 1
	test/xcount == 2

	# Further depths.
	elements = td.fs_snapshot(depth=2)
	test/len(elements) == 4

	sub = [x for x in elements if x[2]['identifier'] == 'subdir'][0][1]
	test/len(sub) == 2
	sub = [x for x in elements if x[2]['identifier'] == 'nesting'][0][1]
	test/len(sub) == 1
	test/len(sub[0][1]) == 0

	elements = td.fs_snapshot(depth=3)
	sub = [x for x in elements if x[2]['identifier'] == 'nesting'][0][1]
	test/len(sub[0][1][0][1]) == 0

	elements = td.fs_snapshot(depth=4)
	sub = [x for x in elements if x[2]['identifier'] == 'nesting'][0][1]
	test/len(sub[0][1][0][1][0][1]) == 0

def test_Path_fs_alloc(test):
	"""
	# - &module.Path.fs_alloc
	"""
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	f = td + [str(i) for i in range(10)]

	f.fs_alloc()
	test/f.fs_type() == 'void'
	test/f.container.fs_type() == 'directory'

	# No effect. Cover case where leading path exists.
	f.fs_alloc()
	test/f.fs_type() == 'void'

	# No effect. Cover case where final entry exists as a file.
	f.fs_store(b'data')
	f.fs_alloc()
	test/f.fs_type() == 'data'

	# No effect. Cover case where final entry exists as a directory.
	f = f * 'a'
	f.fs_mkdir()
	f.fs_alloc()
	test/f.fs_type() == 'directory'

def test_Path_fs_require_void(test):
	"""
	# - &module.Path.fs_require
	# - &module.RequirementViolation

	# Validate that missing file cases are handled.
	"""
	os.umask(0o022)
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	fnf = td/'no-such-file'

	#! Default expects file to be available.
	try:
		(fnf).fs_require()
	except module.RequirementViolation as rv:
		test/rv.r_violation == 'void'
		test/rv.r_type == None
		test/rv.r_properties == ''
		test.isinstance(str(rv), str)
	else:
		self.fail("expected RequirementViolation")

	#! Type is irrelevant, file must be present.
	try:
		(fnf).fs_require(type='socket')
	except module.RequirementViolation as rv:
		test/rv.r_violation == 'void'
		test/rv.r_type == 'socket'
		test/rv.r_properties == ''
		test.isinstance(str(rv), str)
	else:
		self.fail("expected RequirementViolation")

	#! Allows missing files.
	test/(fnf).fs_require(type='void') == fnf
	test/(fnf).fs_require('!') == fnf

	#! Void option.
	test/(fnf).fs_require('x!') == fnf
	test/(fnf).fs_require('@x!') == fnf
	test/(fnf).fs_require('rwx!') == fnf
	test/(fnf).fs_require('x!', type='directory') == fnf
	test/(fnf).fs_require('x!', type='socket') == fnf

def test_Path_fs_require_type(test):
	"""
	# - &module.Path.fs_require
	# - &module.RequirementViolation

	# Validate that fs_require checks the type.
	"""
	os.umask(0o022)
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	df = (td/'data-files')
	df.fs_store(b'nothing')

	#! Type keyword parameter.
	test/td.fs_require(type='directory') == td
	test/df.fs_require(type='data') == df

	#! Type code.
	test/td.fs_require('/') == td
	test/df.fs_require('.') == df

	#! Type mismatch.
	try:
		test/df.fs_require(type='directory') == df
	except module.RequirementViolation as rv:
		test/rv.r_violation == 'type'
		test/rv.r_type == 'directory'
		test/rv.r_properties == ''
		test/rv.fs_path == df
		test.isinstance(str(rv), str)
	else:
		test.fail("expected RequirementViolation")

def test_Path_fs_require_permissions(test):
	"""
	# - &module.Path.fs_require
	# - &module.RequirementViolation

	# Validate that fs_require checks the properties.
	"""
	os.umask(0o022)
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	df = (td/'data-files')
	df.fs_store(b'nothing')

	#! Success cases with type.
	test/td.fs_require('x', type='directory') == td
	test/df.fs_require('rw', type='data') == df

	#! Prohibited case with type.
	try:
		df.fs_require('x', type='data')
	except module.RequirementViolation as rv:
		test/rv.r_violation == 'prohibited'
		test/rv.fs_path == df
		test/rv.fs_type == df.fs_type()
		test.isinstance(str(rv), str)
	else:
		test.fail("expected RequirementViolation")

def test_Path_fs_require_directory_control(test):
	"""
	# - &module.Path.fs_require
	# - &module.RequirementViolation

	# Validate that fs_require allows for optional directory.
	"""
	os.umask(0o022)
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	df = (td/'data-files')
	df.fs_store(b'nothing')
	dirf = (td/'directory').fs_mkdir()

	#! Directory allowed.
	test/df.fs_require('*r/') == df
	test/dirf.fs_require('*r/') == dirf

	#! Directory not allowed.
	try:
		dirf.fs_require('*r')
	except module.RequirementViolation as rv:
		# Unqualified (type) requirement restricts directories.
		test/rv.r_violation == 'directory'
		test/rv.r_properties == 'r'
		test/rv.fs_type == 'directory'
		test.isinstance(str(rv), str)
	else:
		test.fail("expected RequirementViolation")

	#! Directory required (leading slash).
	try:
		df.fs_require('/r')
	except module.RequirementViolation as rv:
		# Unqualified (type) requirement restricts directories.
		test/rv.r_violation == 'type'
		test/rv.r_properties == 'r'
		test/rv.fs_type == 'data'
		test.isinstance(str(rv), str)
	else:
		test.fail("expected RequirementViolation")

def test_Path_fs_require_accessibility(test):
	"""
	# - &module.Path.fs_require
	# - &module.RequirementViolation

	# Validate that the implied accessibility constraint is
	# communicated when paths traverse through regular files or
	# directories without the necessary permissions.
	"""
	os.umask(0o022)
	td = test.exits.enter_context(module.Path.fs_tmpdir())
	df = (td/'data-file')
	df.fs_store(b'nothing')

	#! Traverse through data file.
	try:
		(df/'subfile').fs_require()
	except module.RequirementViolation as rv:
		# Path traversed through a regular file.
		test/rv.r_violation == 'inaccessible'
		test/rv.fs_type == 'unknown'
		test.isinstance(str(rv), str)
	else:
		test.fail("expected RequirementViolation")

	#! Allow traversal through data file.
	test/(df/'subfile').fs_require('*?') == (df/'subfile')

def test_root_instance(test):
	# root is a potential corner case, so give it special attention.
	test/module.root.fs_type() == 'directory'
	test/(+(module.root)).fs_type() == 'directory'

def test_Path_fs_path_string(test):
	"""
	# - &module.Path.fs_path_string

	# Validate path normalization by making sure partitions
	# are properly eliminated.
	"""

	test/module.root.fs_path_string() == '/'

	a = module.root/'a'
	test/a.fs_path_string() == '/a'
	b = a/'b'
	test/b.fs_path_string() == '/a/b'
	c = b.delimit()/'c'
	test/c.fs_path_string() == '/a/b/c'

	test/(module.root@'//test//parted//path//').fs_path_string() == '/test/parted/path'
	test/(module.root@'////////').fs_path_string() == '/'
