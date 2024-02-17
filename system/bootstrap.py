"""
# Bootstrapping for applications that depend on the &..system.factors loader.

# [ Rationale ]

# While (corpus)`fault.io/python` has alignment with the standard filesystem module
# protocol, `sys.path` compatible directory structure, it is preferred to load from
# the compiled bytecode when available so that any construction context dependent
# features are available to applications and so that the fault python context project is
# available under &.system.factors.context.
"""
import types
import sys
from os.path import join

from marshal import load as Load
from builtins import exec as Execute
from builtins import compile as Compile

pkglist = ['context', 'system', 'route', 'project']
modlist = [
	'context.tools',
	'context.types',
	'context.string',

	'route.rewrite',
	'route.core',
	'route.types',
	'system.files',

	'project.types',
	'project.system',
	'project.polynomial',

	'system.factors', # Must be final.
]

def package_import(bytecode, path, root, pkg):
	prefix = root + '.'
	name = prefix + pkg
	fdir = join(path, root, pkg)
	src = join(fdir, '__init__.py')
	return name, fdir, src, bytecode(path, name + '.__init__')

def module_import(bytecode, path, root, mod):
	prefix = root + '.'
	name = prefix + mod
	pj, factor = mod.split('.')
	fdir = join(path, root, pj)
	src = join(fdir, factor + '.py')
	return name, prefix + pj, src, bytecode(path, name)

def load_code(name, bc, src):
	"""
	# Given a marshalled bytecode path and source file, load or compile whichever
	# resource is available prioritizing the compiled form.

	# &name is ignored but required in order to allow overrides to use it
	# as a key instead of the file paths.
	"""
	try:
		f = open(bc, 'rb')
	except FileNotFoundError:
		with open(src) as f:
			return Compile(f.read(), src, 'exec')
	else:
		with f:
			return Load(f)

def install_packages(rename, modules, bytecode, path, root, package_list):
	"""
	# Allocate new package module instances and assign them into &modules.
	"""

	fault_pkg = types.ModuleType(root)
	fault_pkg.__path__ = [path]
	fault_pkg.__file__ = path + '/__init__.py'
	modules[root] = fault_pkg

	f = (lambda x: package_import(bytecode, path, root, x))
	for pkg, mpath, src, bc in map(f, package_list):
		name = rename(pkg)
		m = types.ModuleType(name)
		code = load_code(m.__name__, bc, src)
		m.__path__ = [mpath]
		m.__file__ = src
		m.__cache__ = bc

		Execute(code, m.__dict__)
		modules[m.__name__] = m
		yield m

def install_modules(rename, modules, bytecode, path, root, module_list):
	"""
	# Allocate new module instances and assign them into &modules.
	"""
	f = (lambda x: module_import(bytecode, path, root, x))
	for mod, pkg, src, bc in map(f, module_list):
		name = rename(mod)
		m = types.ModuleType(name)
		m.__file__ = src
		m.__package__ = rename(pkg)
		m.__cache__ = bc

		code = load_code(m.__name__, bc, src)
		Execute(code, m.__dict__)
		modules[m.__name__] = m
		yield m

install_operations = [
	(install_packages, pkglist),
	(install_modules, modlist),
]

def install(modules, bytecode, path, root, Rename=(lambda x: x)):
	"""
	# Install the bootstrap factors into &modules. Normally, &sys.modules.
	"""
	for install_method, seq in install_operations:
		yield from install_method(Rename, modules, bytecode, path, root, seq)

def finish(factors, finder, modules, Rename=(lambda x: x)):
	"""
	# Given an activated &..system.factors module, assign specs and loaders to the previously
	# bootstrapped modules and to the factors module itself.
	"""
	# Finish bootstrapping by providing specs.
	for module in modules:
		module.__spec__ = finder.find_spec(Rename(module.__name__), None)
		module.__loader__ = module.__spec__.loader
		module.__file__ = module.__spec__.origin

	factors.__spec__ = finder.find_spec(Rename(factors.__name__), None)
	factors.__loader__ = factors.__spec__.loader
	factors.__file__ = factors.__spec__.origin

def integrate(faultpath, faultname, faultform,
		images, system, python, arch, form,
		*products,
		modules=sys.modules
	):
	"""
	# Integrate the factor environment into Python's import system.
	"""

	def bytecode(fault, name, sia=system + '-' + python, form=form, suffix='.i'):
		return join(fault, images, sia, *name.split('.')) + suffix

	*requirements, factors = install(modules, bytecode, faultpath, faultname)
	finder = factors.setup(form=form, paths=[faultpath], platform=(system, python, arch))
	finish(factors, finder, requirements)
	for x in products:
		finder.connect(factors.files.Path.from_absolute(x))

	return factors
