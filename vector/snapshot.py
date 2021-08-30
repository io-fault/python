"""
# Parsing and serialization functions for system argument vector snapshots.
"""
from ..context import string

def parse(text:str) -> tuple[
		list[tuple[str, str]],
		str,
		list[str]
	]:
	"""
	# Parse a System Execution Plan string into structured environment
	# settings, executable path, and command arguments.
	"""
	header, *body = text.strip().split('\n\t') # Env + Exe, Command Arguments.
	*env, exe = header.split('\n') # Separate environment settings and executable.
	if env and env[0][:2] == '#!':
		del env[:1]

	parameters = []

	for f in body:
		if f[:1] == ':':
			# Filter empty.
			parameters.extend(x for x in f[1:].split(' ') if x)
		elif f[:1] == '|':
			parameters.append(f[1:])
		elif f[:1] == '-':
			parameters.append(exe)
		elif f[:1] == '\\':
			try:
				nlines, suffix = f.split(' ', 1)
				nlines = nlines.count('n')
			except ValueError:
				nlines = f[1:].count('n')
				suffix = ''
			parameters[-1] += (nlines * '\n')
			parameters[-1] += suffix
		else:
			raise ValueError("unknown argument field qualifier")

	return ([tuple(x.split('=', 1)+[None])[:2] for x in env], exe, parameters)

def serialize(triple, limit=8) -> str:
	"""
	# Serialize the environment, execution path, and command arguments into a string.
	"""

	env, exe, args = triple

	out = ""
	for env, val in env:
		if val is None:
			yield env
		else:
			out += env + '=' + val
			yield env + '=' + val

		yield '\n'

	yield exe
	yield '\n'

	for f in args:
		if '\n' in f:
			fs = list(string.varsplit('\n', f))
			yield '\t|'
			yield fs[0]
			yield '\n'

			for count, suffix in zip(fs[1::2], fs[2::2]):
				yield '\t\\' + ('n' * count)
				if suffix:
					yield ' ' + suffix
				yield '\n'
		else:
			yield '\t|'
			yield f
			yield '\n'
