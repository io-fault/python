"""
# - &.factory

# polynomial-1 materialization checks.
"""
from ...project import factory as module
from ...project import types
from ...system import files
from ...route.types import Segment

from ...project.system import structure_project_declaration

s_information = types.Information(
	identifier = 'http://sample.fault.io/corpus/project',
	name = 'project',
	authority = 'fault.io',
	contact = 'http://fault.io/critical',
)

s_formats = {
	'http://if.fault.io/factors/meta': [
		('chapter', 'txt', 'fault-1', 'kleptic'),
	],
	'http://if.fault.io/factors/system': [
		('elements', 'c', '2011', 'c'),
	],
	'http://if.fault.io/factors/python': [
		('module', 'py', 'psf-v3', 'python'),
	],
}

def test_Composition_indirect(test):
	"""
	# - &module.Composition.indirect
	"""
	Type = module.Composition
	c = Type.indirect('ext', 'source-data')
	test/c.type == None
	test/c.sources == [('ext', 'source-data')]
	test/tuple(c.requirements) == ()

def test_Composition_explicit(test):
	"""
	# - &module.Composition.explicit
	"""
	Type = module.Composition

	c = Type.explicit('f-type', [], [('src.1', "source-data-1"), ('src.2', "source-data-2")])
	test/c.type == 'f-type'
	test/c.sources[0] == ('src.1', "source-data-1")
	test/c.sources[1] == ('src.2', "source-data-2")
	test/tuple(c.requirements) == ()

	# Check symbol presence and empty sources.
	c = Type.explicit('f-type', ['sym-1', 'sym-2'], [])
	test/c.type == 'f-type'
	test/c.sources == []
	test/tuple(c.requirements) == ('sym-1', 'sym-2')

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

def test_plan_cell_factors(test):
	"""
	# - &module.plan

	# Check that plan produces a suffixed path for an indirectly typed factor
	# when given a Cell as the source list.
	"""

	s = [(types.factor@'sfact', module.Composition.indirect('txt', 'chapter-text-content'))]
	infra, f, = module.plan(None, s_formats, s)
	test/tuple(f[0]) == ('sfact.txt',)
	test/f[1] == 'chapter-text-content'

def test_plan_explicitly_typed_factors(test):
	"""
	# - &module.plan
	"""

	s = [(types.factor@'typedfact', module.Composition.explicit('executable', [], [('test.c', 'nothing')]))]
	infra, dotfactor, factorsource = module.plan(None, s_formats, s)

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
	infra, dotfactor, factorsource = module.plan(None, s_formats, s)

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

	ext = module.types.Extensions(None, None)
	fp = module.Parameters(s_information, s_formats, [], extensions=ext)
	module.instantiate(fp, d)

	test/(d@'.project/f-identity').fs_type() == 'data'
	test/(d@'.project/polynomial-1').fs_type() == 'data'

	check_information(test, s_information, (d@'.project/f-identity').get_text_content())

def test_Parameters_instantiate_dimensions(test):
	"""
	# - &module.Parameters.instantiate

	# Validate that dimensions is forwarded by instantiate.
	"""
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	ext = module.types.Extensions(None, None)
	fp = module.Parameters(s_information, s_formats, [], extensions=ext)
	module.instantiate(fp, d, 'd-1', 'd-2')

	serialized = (d@'.project/f-identity').get_text_content()
	sproto, i = structure_project_declaration(serialized)

	expected_id = s_information.identifier + '//' + '/'.join(('d-1', 'd-2'))
	test/expected_id == i.identifier

def test_Parameters_define(test):
	"""
	# - &module.Parameters.define
	"""
	F = module.types.factor
	d = test.exits.enter_context(files.Path.fs_tmpdir())

	fp = module.Parameters.define(s_information, s_formats,
		soles=[('pmodule', F@'python.module', b"data")],
		sets=[
			('lib', 'library', ('symbol',), [('file.c', b"f-content")]),
			('exe', 'executable', (), [('exe-file.c', b"exe-content")]),
		],
	)

	test/fp.factors[0] == (F@'pmodule', module.Composition.indirect('py', b"data"))
	test/fp.factors[1] == (
		F@'lib',
		module.Composition('library', ['symbol',], [
			('file.c', b'f-content')
		])
	)

	test/fp.factors[2] == (
		F@'exe',
		module.Composition('executable', [], [
			('exe-file.c', b'exe-content')
		])
	)

def test_Parameters_define_index_error(test):
	"""
	# - &module.Parameters.define
	"""

	define_keyerr = (lambda: module.Parameters.define(
		s_information, s_formats,
		soles=[('test', 'fake-python-module', '-')],
		sets=[],
	))

	test/KeyError ^ define_keyerr
