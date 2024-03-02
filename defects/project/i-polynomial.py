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

def test_V1_isource(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({})

	vf = (td/'valid.c').fs_init()
	test/p.isource(vf) == True

	invalid = (td/'filename').fs_init()
	test/p.isource(invalid) == False

	dotfile = (td/'.filename').fs_init()
	test/p.isource(dotfile) == False

def test_V1_collect_explicit_sources(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({})
	typcache = p.source_format_resolution()
	unknown = module.unknown_factor_type

	vf = (td/'valid.c').fs_init()
	sub = (td@"path/to/inner.c").fs_init()

	ls = list(p.collect_explicit_sources(typcache, td))
	test/((unknown, vf) in ls) == True
	test/((unknown, sub) in ls) == True

def test_V1_iterfactors_explicit_known(test):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	p = module.V1({'source-extension-map': extmap})

	vf = (td/'valid.c').fs_init()
	pt = (td/'project.txt').fs_init()
	py = (td/'test.py').fs_init()

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

	ft = (td/'cf'/'.factor').fs_init(mkfactor(str(exe_typref), set()).encode('utf-8'))

	v = (td/'cf'/'src'/'valid.c').fs_init()
	fs = dict(p.iterfactors(types.fpc, td, types.factor))

	cf = types.FactorPath.from_sequence(['cf'])
	fls = list(fs[(cf, exe_typref)][-1])
	test/len(fls) == 1
	(module.unknown_factor_type, v) in test/fls
