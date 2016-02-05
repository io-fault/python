"""
Manage system core dumps.

Provides access to core-file location after process exits and controlling
the limits of core file sizes produced by the system. For systems
that do not have &resource modules, the functionality is essentially
a no-op and performs empty functions in order to allow existing code to work.

[ Properties ]

/available
	Whether or not core-file controls is available.
"""
import sys
import os
import os.path
import contextlib
import functools

try:
	import resource
	available = True
except ImportError:
	available = False
	import types
	resource = types.ModuleType("resource",
		"! WARNING:\n\tThis platform does not have the resource module.")
	del types
	def nothing(*args):
		pass
	resource.getrlimit = nothing
	resource.setrlimit = nothing
	resource.RLIMIT_CORE = 0
	del types, nothing

# Replace this with a sysctl c-extension
if os.path.exists('/proc/sys/kernel/core_pattern'):
	def kernel_core_pattern():
		with open('/proc/sys/kernel/core_pattern') as f:
			return f.read()
elif 'freebsd' in sys.platform or 'darwin' in sys.platform:
	def kernel_core_pattern():
		import subprocess
		p = subprocess.Popen(('sysctl', 'kern.corefile'),
			stdout = subprocess.PIPE, stderr = None, stdin = None)
		corepat = p.stdout.read().decode('utf-8')
		prefix, corefile = corepat.split(':', 1)
		return corefile.strip()
else:
	def kernel_core_pattern():
		raise RuntimeError("cannot resolve coredump pattern for this platform")

def location(pid, pattern = functools.partial(os.environ.get, 'COREPATTERN', '/cores/core.{pid}')):
	"""
	Given a process identifier, 
	"""
	import getpass
	return pattern().format(**{'pid': pid, 'uid': os.getuid(), 'user': getpass.getuser(), 'home': os.environ['HOME']})

@contextlib.contextmanager
def constraint(
		limit:int=-1,

		getrlimit=resource.getrlimit,
		setrlimit=resource.setrlimit,
		rtype=resource.RLIMIT_CORE
	):
	"""
	Constrain core dumps during the execution of the context. Useful for managing tests that may dump core.
	Alternatively, &enabled and &disabled can be used as shorthands for clarity.

	! WARNING:
		&constraint is *not* thread safe.
		Conccurrent execution will render inconsistent effects on the limit.

	When executed on systems where &available is `False`, &constrain does nothing.

	Typical use:

	#!/pl/python
		with libcore.constrain(None):
			...

	Core dumps can disabled by designating zero size:

	#!/pl/python
		with libcore.constrain(0):
			...

	[ Parameters ]

	/limit
		The limit of the core file's size emitted by the system.
		A size of `0` will disable core files from being generated.
	"""

	if size_limit is None:
		size_limit = -1
	else:
		size_limit = size_limit or 0

	try:
		current = getrlimit(rtype)
		setrlimit(rtype, (size_limit, size_limit))
		yield None
	finally:
		setrlimit(rtype, current)

enabled = functools.partial(constraint, -1)
disabled = functools.partial(constraint, 0)
