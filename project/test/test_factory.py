"""
# - &.factory

# polynomial-1 materialization checks.
"""
from .. import factory as module
from .. import types
from .. import struct
from ...system import files
from ...route.types import Segment

from ..system import structure_project_declaration

s_information = types.Information(
	identifier = 'http://sample.fault.io/corpus/project',
	name = 'project',
	icon = {},
	authority = 'fault.io',
	contact = 'http://fault.io/critical',
	abstract = None,
)

s_infrastructure = [
	('*.txt', [
		types.Reference('http://if.fault.io/factors', 'chapter', 'type', 'kleptic'),
	]),
	('*.c', [
		types.Reference('http://if.fault.io/factors', 'system', 'type', 'c'),
		types.Reference('http://fault.io/integration/probes//test', 'some-library'),
	]),
]

def test_Composition_indirect(test):
	"""
	# - &module.Composition.indirect
	"""
	Type = module.Composition
	c = Type.indirect('ext', 'source-data')
	test/c.type == None
	test/c.sources == [('ext', 'source-data')]
	test/tuple(c.symbols) == ()

def test_Composition_explicit(test):
	"""
	# - &module.Composition.explicit
	"""
	Type = module.Composition

	c = Type.explicit('f-type', [], [('src.1', "source-data-1"), ('src.2', "source-data-2")])
	test/c.type == 'f-type'
	test/c.sources[0] == ('src.1', "source-data-1")
	test/c.sources[1] == ('src.2', "source-data-2")
	test/tuple(c.symbols) == ()

	# Check symbol presence and empty sources.
	c = Type.explicit('f-type', ['sym-1', 'sym-2'], [])
	test/c.type == 'f-type'
	test/c.sources == []
	test/tuple(c.symbols) == ('sym-1', 'sym-2')

def check_information(test, original, serialized):
	proto, i = structure_project_declaration(serialized)
	test/i == original

def test_plan_information(test):
	"""
	# - &module.plan

	# Check that serialized project information is consistent.
	"""
	dotproject, = module.plan(s_information, None, [])
	check_information(test, s_information, dotproject[1])

def check_infrastructure(test, original, serialized):
	ctx, data = struct.parse(serialized)
	fragment = (lambda x: '#' + x if x is not None else '')
	key = (lambda x: x[-1])

	for k, v in dict(original).items():
		re_symfactors = list(data[k])
		in_symfactors = [
			('absolute', x.method, x.project + '/' + str(x.factor) + fragment(x.isolation))
			for x in v
		]

		re_symfactors.sort(key=key)
		in_symfactors.sort(key=key)
		test/re_symfactors == in_symfactors

def test_plan_infrastructure(test):
	"""
	# - &module.plan

	# Check that serialized infrastructure is consistent.
	"""

	infra_f, = module.plan(None, s_infrastructure, [])
	check_infrastructure(test, s_infrastructure, infra_f[1])

def test_plan_cell_factors(test):
	"""
	# - &module.plan

	# Check that plan produces a suffixed path for an indirectly typed factor
	# when given a Cell as the source list.
	"""

	s = [(types.factor@'sfact', module.Composition.indirect('txt', 'chapter-text-content'))]
	infra, f, = module.plan(None, s_infrastructure, s)
	test/tuple(f[0]) == ('sfact.txt',)
	test/f[1] == 'chapter-text-content'

def test_plan_explicitly_typed_factors(test):
	"""
	# - &module.plan
	"""

	s = [(types.factor@'typedfact', module.Composition.explicit('executable', [], [('test.c', 'nothing')]))]
	infra, dotfactor, factorsource = module.plan(None, s_infrastructure, s)

	test/tuple(dotfactor[0]) == ('typedfact', '.factor',)
	test/tuple(factorsource[0]) == ('typedfact', 'test.c')
	test/factorsource[1] == 'nothing'
	test/dotfactor[1].strip() == 'executable'

def test_plan_explicitly_typed_symbols(test):
	"""
	# - &module.plan

	# Check that symbols are stored and are retrievable.
	"""

	s = [(types.factor@'typedfact',
		module.Composition.explicit(
			'executable',
			['requirement-id'],
			[('test.c', 'nothing')],
		)
	)]
	infra, dotfactor, factorsource = module.plan(None, s_infrastructure, s)

	test/tuple(dotfactor[0]) == ('typedfact', '.factor',)
	test/tuple(factorsource[0]) == ('typedfact', 'test.c')
	test/factorsource[1] == 'nothing'
	test/dotfactor[1].strip().split("\n") == ['executable', 'requirement-id']

S = Segment.from_sequence

def test_materialize_mkdir(test):
	"""
	# - &module.materialize
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())
	module.materialize(d, [(S(['test-mkdir']), None)])
	test/(d/'test-mkdir').fs_type() == 'directory'

def test_materialize_link(test):
	"""
	# - &module.materialize
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())
	src = (d/'source').fs_init(b'source-data')

	module.materialize(d, [(S(['test-file-link']), src)])
	test/(d/'test-file-link').fs_load() == src.fs_load()
	test/list((d/'test-file-link').fs_follow_links())[-1] == src

def test_materialize_module(test):
	"""
	# - &module.materialize
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	src = (d/'source').fs_init(b"source-data")
	module_instance = module.ModuleType('random.path')
	module_instance.__file__ = str(src)

	module.materialize(d, [(S(['test-module']), module_instance)])
	test/(d/'test-module').fs_load() == b"source-data"

def test_materialize_bytes(test):
	"""
	# - &module.materialize
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())
	module.materialize(d, [(S(['test-file']), b'\x00\x00data\x01\x01')])
	test/(d/'test-file').fs_load() == b'\x00\x00data\x01\x01'

def test_materialize_strings(test):
	"""
	# - &module.materialize
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())
	module.materialize(d, [(S(['test-file']), 'encoded string')])
	test/(d/'test-file').fs_load() == b'encoded string'

def test_Parameters_instantiate(test):
	"""
	# - &module.Parameters.instantiate
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	fp = module.Parameters(s_information, s_infrastructure, [])
	module.instantiate(fp, d)

	test/(d/'.project').fs_type() == 'data'
	test/(d/'infrastructure.txt').fs_type() == 'data'

	check_information(test, s_information, (d/'.project').get_text_content())
	check_infrastructure(test, s_infrastructure, (d/'infrastructure.txt').get_text_content())

def test_Parameters_instantiate_dimensions(test):
	"""
	# - &module.Parameters.instantiate

	# Validate that dimensions is forwarded by instantiate.
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	fp = module.Parameters(s_information, s_infrastructure, [])
	module.instantiate(fp, d, 'd-1', 'd-2')

	serialized = (d/'.project').get_text_content()
	sproto, i = structure_project_declaration(serialized)

	expected_id = s_information.identifier + '//' + '/'.join(('d-1', 'd-2'))
	test/expected_id == i.identifier

def test_Parameters_define(test):
	"""
	# - &module.Parameters.define
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	fp = module.Parameters.define(s_information, s_infrastructure,
		extensions={'python-module':'py'},
		soles=[('pmodule', 'python-module', b"data")],
		sets=[
			('lib', 'library', ('symbol',), [('file.c', b"f-content")]),
			('exe', 'executable', (), [('exe-file.c', b"exe-content")]),
		],
	)

	test/fp.factors[0] == (module.types.factor@'pmodule', module.Composition.indirect('py', b"data"))
	test/fp.factors[1] == (
		module.types.factor@'lib',
		module.Composition('library', ['symbol',], [
			('file.c', b'f-content')
		])
	)

	test/fp.factors[2] == (
		module.types.factor@'exe',
		module.Composition('executable', [], [
			('exe-file.c', b'exe-content')
		])
	)

def test_Parameters_define_index_error(test):
	"""
	# - &module.Parameters.define
	"""

	define_keyerr = (lambda: module.Parameters.define(
		s_information, s_infrastructure,
		soles=[('test', 'fake-python-module', '-')],
		sets=[],
	))

	test/KeyError ^ define_keyerr
