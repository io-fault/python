"""
# Check bootstrapping operations.
"""
import types
from ...system import files
from ...system import bootstrap

def test_import_constructions(test):
	"""
	# - &bootstrap.package_import
	# - &bootstrap.module_import
	"""
	# Constraint and sanity checks.
	root = 'F'
	path = '/'
	bytecode = (lambda d, module: 'bytecode:' + d + module)

	package_record = bootstrap.package_import(bytecode, path, root, 'project')
	test/package_record == (
		'F.project',
		'/F/project',
		'/F/project/__init__.py',
		'bytecode:/F.project.__init__',
	)

	module_record = bootstrap.module_import(bytecode, path, root, 'project.factor')
	test/module_record == (
		'F.project.factor',
		'F.project',
		'/F/project/factor.py',
		'bytecode:/F.project.factor',
	)

def test_load_code(test):
	"""
	# - &bootstrap.load_code
	"""
	tmp = test.exits.enter_context(files.Path.fs_tmpdir())
	src = tmp/'test-source.py'
	bc = tmp/'test-source.pb'
	src.fs_store(b'print("load-code-test")')

	srcloaded = bootstrap.load_code('test-name', str(bc), str(src))
	test.isinstance(srcloaded, types.CodeType)
	import marshal
	with open(str(bc), 'wb') as f:
		marshal.dump(srcloaded, f)

	bcloaded = bootstrap.load_code('test-name', str(bc), str(src))
	test.isinstance(srcloaded, types.CodeType)

	# Check with source file missing.
	src.fs_void()
	test/src.fs_type() == 'void'
	bcloaded = bootstrap.load_code('test-name', str(bc), str(src))
	test.isinstance(srcloaded, types.CodeType)

def test_integration(test):
	"""
	# - &bootstrap.install_root
	# - &bootstrap.install_packages
	# - &bootstrap.install_modules
	# - &bootstrap.install
	# - &bootstrap.finish
	# - &bootstrap.integrate

	# Test presumes the system project exists under a python/fault context.
	"""
	tmpdir = test.exits.enter_context(files.Path.fs_tmpdir())
	p1 = (tmpdir/'product-1').fs_mkdir()
	p2 = (tmpdir/'product-2').fs_mkdir()
	for x in [p1, p2]:
		(x/'.product').fs_mkdir()
		(x/'.product'/'PROJECTS').fs_store(b'')
		(x/'.product'/'ROOTS').fs_store(b'')
		(x/'.product'/'CONTEXTS').fs_store(b'')

	rename = (lambda x: x.capitalize())
	ctx, sysproject, *path = __name__.split('.')
	from ...system import __file__ as pkgfile
	pkgfile = files.Path.from_absolute(pkgfile)
	faultpath = (pkgfile ** 3)

	from ...system import identity
	sys, pyimp = identity.python_execution_context()
	sys, host = identity.root_execution_context()

	M = {}
	bfactors = bootstrap.integrate(
		str(faultpath), ctx, 'executable', '__f-int__',
		sys, pyimp, host, 'executable',
		str(p1), str(p2),
		modules=M
	)
	# +1 for fault.__init__.
	test/len(M) == (len(bootstrap.pkglist) + len(bootstrap.modlist) + 1)
