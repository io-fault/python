"""
# Tools for building status data from Python exceptions, tracebacks, and frames.
"""
import itertools
import sys
import typing
import linecache

# Probe for ideal code name.
try:
	import operator
	if hasattr(compile('pass', 'qualname.py', 'exec'), 'co_qualname'):
		codename = operator.attrgetter('co_qualname')
	else:
		codename = operator.attrgetter('co_name')
except (NameError, SyntaxError, ImportError):
	def codename(co, hasattr=hasattr):
		if hasattr(co, 'co_qualname'):
			return co.co_qualname
		if hasattr(co, 'co_name'):
			return co.co_name
		return ''

def line_syntax_area(start, stop=None):
	"""
	# Construct a syntax area representing the given line range.
	# If &stop is &None or equal to &start, the returned area will
	# represent a single line.
	"""
	if stop in {None, start}:
		stop = start + 1

	return [start, 0, stop, 0]

if hasattr(compile('pass', 'qualname.py', 'exec'), 'co_positions'):
	def syntax_area(co, ixn, start, stop=None):
		"""
		# Translate the instruction index to the syntax area that represents
		# the instruction, &ixn.
		"""
		return map_instruction_position(co, ixn, start, stop=stop)
else:
	def syntax_area(co, ixn, start, stop=None):
		return line_syntax_area(start, stop)

def python_syntax_error_frame(instance, name=None):
	"""
	# Extract virtual frame from a Python &SyntaxError.
	"""
	try:
		ecn = instance.end_offset
		eln = instance.end_lineno
		if ecn:
			ecn -= 1
	except AttributeError:
		eln = instance.lineno + 1
		ecn = 0

	area = [instance.lineno, instance.offset, eln, ecn]
	ident = getattr(instance, 'st_factor', name)
	ctx = getattr(instance, 'st_context', ())
	syntype = getattr(instance, 'st_type', 'python')
	return (ident, None, syntype, instance.filename, area, ctx)

def frames(context):
	"""
	# Get explicit frames from the &context.
	# Prioritizes `traceframes` method.
	"""
	if hasattr(context, 'traceframes'):
		yield from context.traceframes()
	elif isinstance(context, SyntaxError):
		yield python_syntax_error_frame(context)
	else:
		yield from ()

def iterstack(frame):
	"""
	# Construct a generator producing frame-lineno pairs from a stack of frames.
	"""
	f = frame
	while f is not None:
		yield (f, f.f_lineno, f.f_lasti)
		f = f.f_back

def itertraceback(traceback):
	"""
	# Construct a generator producing frame-lineno pairs from a traceback.
	"""
	tb = traceback
	while tb is not None:
		yield (tb.tb_frame, tb.tb_lineno, tb.tb_lasti)
		tb = tb.tb_next

def iterlnotab(lineno:int, encoded:bytes) -> typing.Iterable[typing.Tuple[int, int]]:
	# Construct bytecode address to line number pairs from an encoded co_lnotab field.
	# Currently not used and may be removed.
	ln = lineno
	ba = 0

	for ba_i, ln_i in zip(encoded[0::2], encoded[1::2]):
		ba += ba_i
		ln += ln_i
		yield ba, ln

def syntax(path, start, stop, /, getline=linecache.getline):
	for x in range(start, stop):
		try:
			yield getline(path, x)
		except IndexError:
			pass

def _first(iterlines, start, default):
	for i, line in enumerate(iterlines, start):
		if line and not line.isspace():
			return i

	return default

def trim(lineno, lines):
	"""
	# Strip whitespace only lines from the edges of the sequence.
	"""
	start = _first(lines, 0, 0)
	stop = len(lines) - _first(reversed(lines), 0, len(lines))
	return lineno + start, lines[start:stop]

def map_instruction_position(co, ixn, start, stop=None):
	"""
	# Retrieve the syntax area associated with the instruction, &ixn.
	# Constructs a vector of line-column pairs that use inclusive indexes.

	# A zero column index on the stop indicates end of previous line.
	"""
	for sln, eln, scn, ecn in itertools.islice(co.co_positions(), ixn // 2, None):
		if ecn:
			ecn -= 1

		if ecn == 0 and sln == eln:
			eln += 1
		return [sln, scn, eln, ecn]
	else:
		return line_syntax_area(start, stop)

def element_context_area(filepath, lineno, getline=linecache.getline):
	stop = start = lineno
	l = getline(filepath, start)
	lws = len(l) - len(l.lstrip())
	while l.lstrip()[:1] == '@':
		stop += 1
		l = getline(filepath, stop)

	return [start, lws + 1, stop+1, 0]

def syntaxframe(
		factor, element, syntype,
		filepath, synarea, context=(),
		ctxarea=None, fcontrol=None,
		/, syntaxcontext=1, getline=linecache.getline
	):
	"""
	# Construct a trace frame from the given arguments.
	"""
	fcontrol = None
	fs_path = filepath
	start = synarea[0] - syntaxcontext
	stop = synarea[2] + syntaxcontext
	if synarea[3] == 0:
		stop -= 1

	sym_ctx = (factor, fs_path)
	sym_dec = (element, ctxarea,)

	return (
		[sym_ctx, sym_dec],
		fcontrol, synarea,
		context,
		syntype, [
			[0, []],
			trim(start, list(syntax(fs_path, start, stop)))
		]
	)

def traceframe(pythonframe, /, syntaxcontext=1, getline=linecache.getline):
	"""
	# Represent the given &pythonframe, triple, as a trace frame.
	"""
	f, lineno, ixn = pythonframe
	f_locals = f.f_locals
	fcontrol = f_locals.get('__traceframe__', None)
	f_globals = f.f_globals

	co = f.f_code
	synarea = syntax_area(co, ixn, lineno)

	fs_path = co.co_filename
	earea = element_context_area(fs_path, co.co_firstlineno)
	eln = earea[0]
	epath = codename(co)

	if epath in {'<module>'}:
		epath = None
		el_excerpt = (eln, [])
	else:
		el_excerpt = trim(eln, list(syntax(fs_path, eln, earea[2])))
		# Check whether the element is *currently* addressable.
		if epath not in f_globals:
			i = epath.find('.')
			if i == -1 or epath[:i] not in f_globals:
				# Mark the element as not being addressable.
				epath = '.' + epath

	syntype = (f_globals.get('__syntaxtype__', 'python'))

	start = synarea[0] - syntaxcontext
	stop = synarea[2] + syntaxcontext
	if synarea[3] == 0:
		stop -= 1

	sym_ctx = (f_globals.get('__name__', None), fs_path)
	sym_dec = (epath, earea,)

	# Retrieve marked locals.
	f_ctx = [
		(x, f_locals[x])
		for x in f_globals.get('__tracecontext__', ())
		if x in f_locals
	]

	return (
		[sym_ctx, sym_dec],
		fcontrol, synarea, f_ctx,
		syntype, [
			# excerpt of frame context (method/function)
			el_excerpt,
			# excerpt of frame location
			trim(start, list(syntax(fs_path, start, stop)))
		]
	)

def exception(instance:BaseException, traceback, syntaxcontext=1):
	"""
	# Extract the necessary information for identifying
	# the context and location that the given exception came from.
	"""
	module_name = instance.__class__.__module__
	module_resource_path = getattr(sys.modules[module_name], '__file__', None)

	exc_ctx = (module_name, module_resource_path)
	exc_declaration = (instance.__class__.__qualname__, None)

	if hasattr(instance, 'tracecontext'):
		exc_instance_ctx = instance.tracecontext()
	else:
		exc_instance_ctx = []

	try:
		if isinstance(instance, SyntaxError):
			# Special case syntax errors in order to eliminate information
			# redundancy with explicit frames.
			exc_msg = [instance.msg + "\n"]
		else:
			exc_msg = str(instance).splitlines(True)
	except:
		exc_msg = "(exception class failed to formulate the message text)"

	exc_trace = [traceframe(x, syntaxcontext=syntaxcontext) for x in itertraceback(traceback)]

	# Primarily for SyntaxErrors, but any application tracing as well.
	exc_trace.extend([
		syntaxframe(*x, syntaxcontext=syntaxcontext)
		for x in frames(instance)
	])

	# Including grouped exceptions.
	if hasattr(instance, 'exceptions') and instance.exceptions:
		xgroup = [
			# Conditionally process to allow already transformed
			# exceptions to be passed through directly.
			failure(x) if isinstance(x, BaseException) else x
			for x in instance.exceptions
		]
	else:
		xgroup = None

	if instance.__context__ is not None:
		xchain = failure(instance.__context__)
	else:
		xchain = None

	return (([exc_ctx, exc_declaration], exc_msg, exc_instance_ctx, exc_trace), xchain, xgroup)

def failure(error:BaseException, trace=None, /, hasattr=hasattr):
	"""
	# Transform the exception and its trace into a serializable data structure.
	"""
	exc_v = []

	while error is not None:
		exc_v.append(exception(error, trace or error.__traceback__))
		error = error.__cause__

	return exc_v

def fframe(index, factor, element, resource, area, level=0):
	if element is None:
		factorpath = ' ' + str(factor) if factor else ''
	else:
		factorpath = ' ' + '.'.join((factor, element))

	if area[0] == area[2] or (area[0]+1 == area[2] and area[3] == 0):
		lines = str(area[0])
	else:
		lines = '-'.join(map(str, area[0::2]))

	return [
		(level, f"[#{index}{factorpath}]\n"),
		(level, f"{resource}:{lines}\n"),
	]

def ftrace(frames, marks={}, exclude={'fault-contention'}, space=("\t", "  ", 2), level=0, iframes=iter):
	ic, rc, rl = space
	fnum = 0
	nframes = len(frames)

	for (sym_ctx, sym_dec), fctl, area, ctx, syntype, excerpts in iframes(frames):
		fnum += 1
		if fctl in exclude:
			continue

		resource = sym_ctx[1]
		yield from fframe(fnum, sym_ctx[0], sym_dec[0], resource, area, level=level)

		#* WARNING: Presuming one level of context.
		(ctxln, ctxlines), (xlineno, xlines) = excerpts

		nclines = len(ctxlines)
		nxlines = len(xlines)
		maxl = max(len(str(xlineno + nxlines)), 4)

		if nclines:
			for ln, l in enumerate(ctxlines, ctxln):
				lns = str(ln).rjust(maxl, " ")
				l = l.replace(ic, rc)

				yield (level, f"   {lns}: {l}")

			if nxlines:
				delta = str((ctxln + nclines) - xlineno).rjust(maxl, " ")
				yield (level, f"   {delta}: [=]\n")

		if nxlines:
			eln = area[2]
			if area[3] > 0:
				eln += 1

			lmarks = {i: "->" for i in range(area[0], eln)}
			unmarked = " " * 3

			for ln, l in enumerate(xlines, xlineno):
				lns = str(ln).rjust(maxl, " ")
				# Expand literal indentations.
				lr = l.replace(ic, rc)

				if ln in lmarks:
					prefix = lmarks[ln].rjust(3, " ")
				else:
					prefix = unmarked

				yield (level, "".join((prefix, lns, ": ", lr)))

				# If the span has a non-zero range, insert a caret line.
				index = marks.get((resource, ln), 0)
				if index:
					re = l[:index].count(ic)
					index -= re
					index += (re * rl)
					yield (level, " "*(maxl + 3) + ": " + (index * " ") + "^" + "\n")

		for x in ctx:
			yield (level, ": ".join(x) + "\n")

def fcontexts(xorigin, xdirectory, level=0, ichain=reversed):
	if xdirectory:
		yield (level, "-> Exception Directory:\n")
		for x in xdirectory:
			yield from fchain(x, level=level, ichain=ichain)

	if xorigin:
		# Format after directory to reduce distance from the leading exception.
		yield (level, "-> Exception chained from the following:\n")
		yield from fchain(xorigin, level=level, ichain=ichain)

def fexcept(exception, level=0, ichain=reversed):
	((exc_ctx, exc_dec), exc_msg, ictx, xtrace) = exception

	# Trace above exception title and message.
	yield from ftrace(xtrace, level=level)

	if exc_ctx[0] == 'builtins':
		# Identify exception as a coreword.
		excid = exc_dec[0]
	else:
		excid = '.'.join((exc_ctx[0], exc_dec[0]))

	if not exc_msg:
		yield (level, excid + '\n')
	else:
		if not exc_msg[-1].endswith('\n'):
			exc_msg[-1] = exc_msg[-1] + '\n'

		yield (level, excid + ': ' + exc_msg[0])
		for l in exc_msg[1:]:
			yield (level, l)

def fchain(fexceptions, level=0, ichain=reversed):
	i = ichain(fexceptions)

	x, *ext = next(i)
	yield from fcontexts(*ext, level=level+1, ichain=ichain)
	yield from fexcept(x, level=level, ichain=ichain)

	for x, *ext in i:
		yield (level, ':\n')
		yield (level, ': Former exception explicitly caused the latter.\n')
		yield (level, ':\n')
		yield from fcontexts(*ext, level=level+1, ichain=ichain)
		yield from fexcept(x, level=level, ichain=ichain)

def format(fexceptions, indent="\t", prefix='| ', level=0, ichain=reversed):
	for il, line in fchain(fexceptions, level=level, ichain=ichain):
		yield prefix.join((indent * il, line))

def hook(e, v, tb):
	"""
	# &sys.excepthook implementation using &format and &failure.
	"""
	fstruct = failure(v, tb)
	sys.stderr.writelines(format(fstruct))
	sys.stderr.flush()
