"""
# Prepare the fault context package for use after downloading the context package.

# This manages the relocation of the context project directory into an actual context-factor
# directory. Normally, similar to (system/shell)`mkdir fault && mv context fault/`, but
# with some constraints in order to make sure that the move wasn't already performed.
"""
# This script may be used prior to the fault package existing,
# so relative imports must be avoided.
import os
import os.path
import sys

def mkctxpkg(root_init, name='fault'):
	dirname = os.path.dirname
	exists = os.path.exists
	lexists = os.path.lexists
	join = os.path.join
	readlink = os.readlink

	ctxdir = dirname(root_init)
	parent = dirname(ctxdir)
	outer_init = join(parent, '__init__.py')

	if lexists(outer_init):
		if not exists(outer_init):
			pass
		else:
			print('! NOTE:', outer_init, 'already exists.')

			lpath = readlink(outer_init)
			if not os.path.isabs(lpath):
				# handle relative link
				lpath = join(dirname(outer_init), lpath)

			if lpath == root.__file__:
				print('! EXIT:', 'Context root is properly linked; exiting without changes.')
				raise SystemExit(0)
			else:
				print('! WARNING:', '%r is not linked to %r' %(outer_init, root.__file__))
	else:
		if exists(outer_init):
			print('! ERROR:', 'context/../__init__.py exists and is not a link to root. Aborting')
			raise SystemExit(200)

	# Link both after creating enclosure.
	fault_dir = join(parent, name)
	if exists(fault_dir):
		print(
			'! ERROR:',
			'%r exists in parent, ' \
			'refusing to enclose "context" ' \
			'for finishing preparation.' %(
				fault_dir,
			)
		)
		raise SystemExit(201)

	print('! STATUS:', 'Creating %r in %r for enclosing project set.' %(fault_dir, parent))
	os.mkdir(fault_dir) # New context enclosure
	pycache = join(fault_dir, '__pycache__')
	os.mkdir(pycache)

	print('! STATUS:', 'Moving context package directory into enclosure.')
	print('\t# %r' %(ctxdir,))
	print('\t# %r' %(join(fault_dir, 'context'),))
	os.rename(ctxdir, join(fault_dir, 'context'))

	root_link_path = 'context/root.py'

	print('! STATUS:', 'Creating symbolic links for context.root.')
	os.symlink(root_link_path, join(fault_dir, '__init__.py'))
	#root_pyc_link_path = '../context/__pycache__/root.pyc'
	#os.symlink(root_pyc_link_path, join(pycache, '__init__.pyc'))

if __name__ == '__main__':
	sys.stdout.close()
	sys.stdout = sys.stderr
	args = sys.argv[1:]
	name, = args
	mkctxpkg(root.__file__, name=name)
