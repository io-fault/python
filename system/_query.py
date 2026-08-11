import os
import operator

from ..context import tools
from . import files

# Keep the parsed forms cached.
_path = tools.cachedcalls(16)(tools.compose(operator.methodcaller('delimit'), files.root.__matmul__))
_dirs = tools.cachedcalls(2)(operator.methodcaller('split', os.pathsep))

def paths(environment:str='PATH') -> files.Path:
	return map(_path, _dirs(os.environ[environment]))

def executables(exename:str, environment:str='PATH') -> files.Path:
	# Isolated to avoid lookup/splitting in cases where the override is not exhausted.
	for x in paths(environment):
		path = x / exename
		typ = path.fs_type()
		if typ != 'void':
			yield path

def home(environment:str='HOME') -> files.Path:
	try:
		return _path(os.environ[environment])
	except (KeyError, TypeError):
		try:
			import pwd
			return _path(pwd.getpwuid(os.getuid()).pw_dir)
		except:
			return None

def username() -> str:
	try:
		import pwd
		return pwd.getpwuid(os.getuid()).pw_name
	except:
		return None

def usertitle() -> str:
	try:
		import pwd
		return pwd.getpwuid(os.getuid()).pw_gecos
	except:
		return None

def shell() -> files.Path:
	try:
		import pwd
		return pwd.getpwuid(os.getuid()).pw_shell
	except:
		return None

def platform(system:str=None, environment:str='F_EXECUTION'):
	from .execution import Platform

	pfe = os.environ.get(environment, '').strip()
	if pfe:
		paths = [(files.root@x) for x in pfe.split(os.pathsep)]
	else:
		h = (home()/'.host')
		if h.fs_type() == 'directory':
			paths = [h]
		else:
			paths = []

	if system is None:
		from . import identity
		system = identity.python_execution_context()[0]

	return Platform.from_system(system, paths)
