"""
# Limited tests as the information retrieved is expected to vary.
"""
from ...system import files
from ...system import query as module

def test_paths(test):
	"""
	# - &module.paths
	"""
	i = module.executable_paths()
	l = list(i)

def test_executable(test):
	"""
	# - &module.executable
	"""
	test/(files.root@"/usr/bin/tee") == module.executable("tee")

def test_executables_cat(test):
	"""
	# - &module.executables
	"""

	i = module.executables('cat')
	l = list(i)
	test/len(l) >= 1 # No cat?

	import sys
	test/sys.getrefcount(i) == 2
	del i
	test.garbage()

def test_executables_rm(test):
	"""
	# - &module.executables
	"""
	i = module.executables('rm')
	l = list(i)
	test/len(l) >= 1 # No rm?

def test_user_identifier(test):
	"""
	# - &module.user
	"""
	import os
	test/module.user() == os.getuid()
	test/module.user('identifier') == os.getuid()

def test_user_name(test):
	"""
	# - &module.username
	"""
	import os
	test/module.username() == module.user('name')
	os.environ['USER'] = 'override' + module.user('name')
	test/module.username() != module.user('name')

def test_user_title(test):
	"""
	# - &module.user
	"""
	title = module.user('title')
	test/title != ''

def test_user_role(test):
	"""
	# - &module.user
	"""
	title = module.user('role')
	test/title != ''

def test_user_shell(test):
	"""
	# - &module.user
	"""
	sh = module.user('shell')
	test.isinstance(sh, files.Path)

def test_user_home(test):
	"""
	# - &module.home
	"""
	import os
	test/module.home() == module.user('home')
	test.isinstance(module.home(), files.Path)
	os.environ['HOME'] = '/'
	test/module.home().fs_path_string() == '/'

def test_ProcessMetrics(test):
	"""
	# - &module.ProcessMetrics

	# Check constructors, operators, and other expectations.
	"""

	Type = module.ProcessMetrics
	zero1 = Type()
	zero2 = Type.from_parts()
	test/zero1 == zero2
	test/False == (zero1 is zero2)

	zstr = str(zero1)
	i = zstr.find('process_count:')
	x = i + len('process_count: ')
	test/zstr[x:x+1] == '0'

	# Check representation cycle. Compensate for factor loader.
	# Preferrable to have the import path here.
	import sys
	from ... import __name__ as n
	from ...system import extensions as ext
	ext.query = module
	from ... import system as fsys
	fsys.extensions = ext
	froot = sys.modules[n]
	froot.system = fsys
	g = {n: froot}
	pm = Type(zero1)
	pm.zombie_count = 20
	pm_repr = eval(repr(pm), g)
	test/pm_repr.zombie_count == 20
	test/pm_repr == pm

	# Mutable attributes.
	zero1.process_count += 100
	test/(zero1 + zero2).process_count == 100

def test_process_usage_scan(test):
	"""
	# - &module.process_usage_scan

	# No validation of coherency; just smoke test.
	"""

	import os
	pm_s = module.process_usage_scan(os.getpid(), 1)
	pm_g = module.process_usage_scan(-os.getpid(), 128)
	pm_g1 = module.process_usage_scan(-os.getpid(), 1)
	test/pm_s != pm_g

def test_process_executable_path(test):
	"""
	# - &module.process_executable_path

	# Validate non-empty return.
	"""

	path = module.process_executable_path
	test/path != ""
