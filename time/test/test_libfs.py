from .. import libfs

def test_stats(test):
	stat = libfs.stat(__file__)
	with open(__file__) as f:
		fstat = libfs.fstat(f.fileno())
	test.fail_if_not_equal(fstat, stat) # potentially a bogus failure
	for x in fstat, stat:
		test.fail_if_not_instance(x.st_atime, libfs.lib.Timestamp)
		test.fail_if_not_instance(x.st_mtime, libfs.lib.Timestamp)
		test.fail_if_not_instance(x.st_ctime, libfs.lib.Timestamp)

if __name__ == '__main__':
	from dev import libtest; libtest.execmodule()
