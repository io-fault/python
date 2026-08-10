"""
# Limited tests as the information retrieved is expected to vary.
"""
from ...system import query as module

def test_paths(test):
	"""
	# - &module.paths
	"""
	i = module.paths()
	l = list(i)

def test_executables_cat(test):
	"""
	# - &module.executables
	"""
	i = module.executables('cat')
	l = list(i)
	test/len(l) >= 1 # No cat?

def test_executables_rm(test):
	"""
	# - &module.executables
	"""
	i = module.executables('rm')
	l = list(i)
	test/len(l) >= 1 # No rm?

def test_username(test):
	"""
	# - &module.username
	"""
	user = module.username()
	test/user != None

def test_usertitle(test):
	"""
	# - &module.usertitle
	"""
	title = module.usertitle()
	test/title != None

def test_shell(test):
	"""
	# - &module.shell
	"""
	sh = module.shell()
	test/sh != None

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
	pm_repr = eval(repr(pm), globals=g)
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
