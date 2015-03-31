import os
import tempfile
from .. import libfs

def test_stats(test):
	stat = libfs.stat(__file__)
	with open(__file__) as f:
		fstat = libfs.fstat(f.fileno())

	test/fstat == stat # potentially a bogus failure
	for x in fstat, stat:
		test/x.st_atime / libfs.library.Timestamp
		test/x.st_mtime / libfs.library.Timestamp
		test/x.st_ctime / libfs.library.Timestamp

def test_modification_time(test):
	'Somewhat of a file system test'
	with tempfile.TemporaryDirectory() as d:
		file = os.path.join(d, 'myfile')
		test/os.path.exists(file) == False
		with open(file, 'w') as f:
			f.write('some data\n')
		test/os.path.exists(file) == True
		mtime1 = libfs.stat(file).st_mtime

		import time
		s = int(time.time())
		while int(time.time()) == s:
			time.sleep(0.05)

		with open(file, 'a') as f:
			f.write('some more data\n')
		mtime2 = libfs.stat(file).st_mtime

		test/mtime2 > mtime1

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
