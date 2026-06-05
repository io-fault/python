"""
# Analyze polynomial using temporary directories.
"""
import itertools

from ...system import files

from ...project import types
from ...project import polynomial as module

python_factor_typref = types.Reference(
	'http://if.fault.io/factors',
	types.factor@'python.module',
	'type',
	'python.psf-v3',
)

text_factor_typref = types.Reference(
	'http://if.fault.io/factors',
	types.factor@'text.chapter',
	'type',
	'kleptic',
)

exe_typref = types.Reference(
	'http://if.fault.io/factors',
	types.factor@'system.executable',
	'type',
	None,
)

extmap = {
	'py': python_factor_typref,
	'txt': text_factor_typref,
}

def mkfactor(ftype, symbols):
	lines = [ftype]
	lines.extend(sorted(symbols))
	return "\n".join(lines)

def refer(fps, context=None):
	return types.fpc(types.factor, fps)

def test_type_declarations(test):
	# Explicit language.
	typdec = module.interpret_type_declaration("type/context", "ftype.ext dialect language", None)
	ext, typref, reqs = typdec
	xtypref = module.types.Reference.from_ri('type', "type/context.ftype")
	xtypref = xtypref.isolate("language.dialect")
	test/ext == "ext"
	test/typref == xtypref
	test/reqs == None

	# Factor type language class; used when the machine is also the language.
	typdec = module.interpret_type_declaration("type/machine", "ftype.ext dialect", None)
	ext, typref, reqs = typdec
	xtypref = module.types.Reference.from_ri('type', "type/machine.ftype")
	xtypref = xtypref.isolate("machine.dialect")
	test/ext == "ext"
	test/typref == xtypref
	test/reqs == None

def test_load_formats(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())

	spec = b"\n"
	spec = b"# Comment\n"
	spec += b"context/system\n"
	spec += b"\telements.1 dia-1 pl-1\n"
	spec += b"\telements.2 dia-2 pl-2\n"
	spec += b"\t\tref-2\n"
	spec += b"\telements.3 dia-3 pl-3\n"
	spec += b"\n"

	# Include an empty context expecting it to be ignored.
	spec += b"context/local\n"
	(td/'formats').fs_alloc().fs_store(spec)

	for i, ts in enumerate(module.load_formats(td/'formats')):
		I = str(i+1)
		ext, typref, typreq = ts
		test/ext == I
		test/typref.project == 'context'
		test/typref.factor == module.types.factor@'system.elements'
		test/typref.format.language == 'pl-' + I
		test/typref.format.dialect == 'dia-' + I
		if typreq:
			test/list(typreq)[0] == 'ref-' + I

def test_V1_type_requirements(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())

	spec = b"type-context\n"
	spec += b"\telements.m 2011 objective-c\n"
	spec += b"\t\tignored\n"
	spec += b"\telements.c 2011 c\n"
	spec += b"\t\ttype-req-ref-1\n\t\ttype-req-ref-2\n"
	spec += b"\telements.cc 2017 c++"

	(td@'.project/polynomial-1').fs_alloc().fs_store(spec)
	(td/'sample.c').fs_store(b'')
	(td/'sample-2.cc').fs_store(b'')

	p = module.V1({})
	p.configure(td)

	factors = p.iterfactors(refer, td, types.factor)
	for fi, fs in factors:
		if fi[0] == types.factor@'sample':
			treq = fs[0]
		elif fi[0] == types.factor@'sample-2':
			zreq = fs[0]

	test/treq == {types.factor@'type-req-ref-1', types.factor@'type-req-ref-2'}
	test/zreq == set()

def test_V1_isource(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({})

	vf = (td/'valid.c').fs_alloc().fs_store(b'')
	test/p.isource(vf) == True

	invalid = (td/'filename').fs_alloc().fs_store(b'')
	test/p.isource(invalid) == False

	dotfile = (td/'.filename').fs_alloc().fs_store(b'')
	test/p.isource(dotfile) == False

def test_V1_collect_explicit_sources(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({})
	typcache = p.source_format_resolution()
	unknown = module.unknown_factor_type

	vf = (td/'valid.c').fs_alloc().fs_store(b'')
	sub = (td@"path/to/inner.c").fs_alloc().fs_store(b'')

	ls = list(p.collect_explicit_sources(typcache, td))
	test/((unknown, vf) in ls) == True
	test/((unknown, sub) in ls) == True

def test_V1_iterfactors_explicit_known(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({'source-extension-map': extmap})

	vf = (td/'valid.c').fs_alloc().fs_store(b'')
	pt = (td/'project.txt').fs_alloc().fs_store(b'')
	py = (td/'test.py').fs_alloc().fs_store(b'')

	idx = dict(p.iterfactors(types.fpc, td, types.factor))
	test/len(idx) == 3
	sources = list(itertools.chain(*[x[-1] for x in idx.values()]))

	(module.unknown_factor_type, vf) in test/sources
	(text_factor_typref, pt) in test/sources

	py_seg = types.FactorPath.from_sequence(['test'])
	py_struct = idx[(py_seg, python_factor_typref.isolate(None))]
	test/py_struct == (set(), [(python_factor_typref, py)])

def test_V1_iterfactors_explicit_unknown(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({'source-extension-map': extmap})

	ft = (td/'cf'/'.factor').fs_alloc().fs_store(mkfactor(str(exe_typref), set()).encode('utf-8'))

	v = (td/'cf'/'src'/'valid.c').fs_alloc().fs_store(b'')
	fs = dict(p.iterfactors(types.fpc, td, types.factor))

	cf = types.FactorPath.from_sequence(['cf'])
	fls = list(fs[(cf, exe_typref)][-1])
	test/len(fls) == 1
	(module.unknown_factor_type, v) in test/fls
