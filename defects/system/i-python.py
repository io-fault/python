"""
# Check the implementation of import routes.
"""
import sys
from ...system import python as module

def test_Import(test):
	# ..bit strange when dealing with nested project packages
	fullpath = __package__.split('.')
	localpath = fullpath[fullpath.index('system'):]
	local = '.'.join(fullpath[:fullpath.index('system')+1])

	# package.test
	r = module.Import.from_fullname(__package__)

	# crawl stack; closest package module is chosen
	test/module.Import.from_context() == r

	test/r.fullname == '.'.join((__package__, ))
	test/r.module() == sys.modules[__package__]
	test/r.container.module() == sys.modules['.'.join(__package__.split('.')[:-1])]

	# stack
	r = module.Import.from_fullname(__package__)
	modules = r.stack()
	test/len(modules) >= len(fullpath)

	test/modules[0] == r.module() # most "significant" module first
	for x in modules:
		test/x == r.module()
		r = r.container

	# module that does not exist
	r = module.Import.from_fullname('+++++nosuch_module')
	test/r.module() == None
	test/r.root == r

def test_Import_real(test):
	# real resolution
	r = module.Import.from_fullname(__package__ + '.' + '+++++nosuch_module')
	test/r.module() == None
	test/r.real() == module.Import.from_fullname(__package__)

def test_Import_from_attributes(test):
	mod, attr = module.Import.from_attributes(__package__)
	test/mod == module.Import.from_fullname(__package__)
	test/attr == ()

def test_Import_tree(test):
	from .. import __name__ as project
	local_module = module.Import.from_fullname(__name__)
	pkg = module.Import.from_fullname(project)
	pkgs, mods = map(set, pkg.tree())

	test/((pkg/'system') in pkgs) == True
	test/(local_module in mods) == True

def test_Import_get_last_modified(test):
	# This is essentally the implementation; the method is mere convenience.
	pkg = module.Import.from_fullname(__package__)
	test/pkg.file().get_last_modified() == pkg.get_last_modified()
