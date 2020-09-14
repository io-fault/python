"""
# Clean the package tree of bootstrap built files.
"""
import os.path
import importlib.machinery

from ...system import python
from ...system import libfactor

ext_suffixes = importlib.machinery.EXTENSION_SUFFIXES

def collect_composites(route):
	is_composite = libfactor.composite
	is_ext = libfactor.python_extension

	package_file = route.file()
	packages, modules = route.tree()
	del modules

	for target in packages:
		tm = importlib.import_module(str(target))
		if is_composite(target) and is_ext(tm):
			yield target

def clear_bootstrap_extensions(route):
	"""
	# Remove the extensions constructed by the bootstrap process.
	"""
	# peel until it's outside the first extensions directory.
	pkg = route
	while pkg.points and pkg.identifier != 'extensions':
		pkg = pkg.container
	names = route.absolute[len(pkg.absolute):]
	pkg = pkg.container

	if pkg.fs_type() == 'void':
		return

	print('[', str(route), ']')
	link_target = pkg.file().container + names
	final = link_target.suffix_filename(ext_suffixes[0])

	removals = []
	for suf in ext_suffixes[1:] + ['.pyd', '.dylib']:
		rmf = link_target.suffix_filename(suf)
		if rmf.fs_type() != 'void':
			removals.append(rmf)

	dsym = link_target.suffix_filename('.so.dSYM')
	if dsym.fs_type() != 'void':
		removals.append(dsym)

	if removals:
		print('/Removed')
		for x in removals:
			print('\t- ' + str(x))
			os.unlink(str(x))

	if final.fs_type() != 'void':
		print()
		print('/Kept')
		print('\t- ' + str(final))

	if link_target.suffix_filename('.py').fs_type() != 'void':
		print('! WARNING: Extension may conflict with Python module:', str(link_target))
	print('')

if __name__ == '__main__':
	import sys
	from ... import context
	sys.stdout.close()
	sys.stdout = sys.stderr
	print('! NOTE: Extensions ending with %r are being kept.' %(ext_suffixes[0],))
	print('')
	rr = python.Import.from_fullname(context.__package__).container
	for pkg in collect_composites(rr):
		clear_bootstrap_extensions(pkg)
