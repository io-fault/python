"""
# Product directory interface checks.
"""
from ...system import files
from ...project import system as module
from ...project.types import factor, FactorIsolationProtocol, Information, Reference

t_project_id = 'http://ni.fault.io/test/project'

def setup(pd, local_id='', project='project'):
	pj = (pd/project).fs_mkdir()
	pid = (t_project_id + local_id)
	what = project + ' ' + pid + ' factors/polynomial-1\n'
	whom = 'fault.io <http://fault.io/critical>\n'
	(pj@'.project/f-identity').fs_alloc().fs_init((what + whom).encode('utf-8'))
	return pj

def product_a(test, name='product'):
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	pdr = (td/name).fs_mkdir()

	ctx = (pdr/'ctx').fs_mkdir()
	setup(ctx, '/first-context', project='context')
	sub = (ctx/'sub').fs_mkdir()
	setup(sub, '/second-context', project='context')
	setup(sub, '/alt-1', project='alt-1')
	setup(sub, '/alt-2', project='alt-2')

	para = (pdr/'parallel').fs_mkdir()
	setup(para, '/parallel', project='parallel')
	return td, module.Product(pdr)

def test_Product_attributes(test):
	"""
	# - &module.Product.project_index_route
	"""
	pd = module.Product(files.root)
	Class = files.root.__class__
	test.isinstance(pd.project_index_route, Class)

def test_Product_import(test):
	"""
	# - &module.Product.import_protocol
	"""
	for name in module.protocols:
		pn = module.Product.import_protocol(name)
		test.issubclass(pn, FactorIsolationProtocol)

def test_iterprojects_root_no_context(test):
	"""
	# - &module.Product.iterprojects
	"""
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	pdr = (td/'product').fs_mkdir()
	setup(pdr)

	pd = module.Product(pdr)
	pj, = pd.iterprojects()
	pid, proto, pjdir = pj

	test/pid == t_project_id
	test/proto == 'factors/polynomial-1'
	test/pjdir == pdr/'project'

def test_update(test):
	"""
	# - &module.Product.update
	"""
	td = test.exits.enter_context(files.Path.fs_tmpdir())
	pdr = (td/'product').fs_mkdir()
	ctx = (pdr/'ctx').fs_mkdir()
	setup(ctx, project='context')

	pd = module.Product(pdr)
	pd.roots = {module.types.factor@'ctx'}
	pd.update()
	cprj = pd.projects

	pd.update()
	test/cprj == pd.projects

def test_update_nested(test):
	"""
	# - &module.Product.update
	"""
	td, pd = product_a(test)
	pd.roots = {module.types.factor@'ctx'}
	pd.update()
	cprj = pd.projects

	pd.update()
	test/cprj == pd.projects

	projects = [
		'/first-context',
		'/second-context',
		'/alt-1',
		'/alt-2',
	]

	for x in projects:
		test/pd.projects << (t_project_id + x)

def test_cache_io(test):
	"""
	# - &module.Product.store
	# - &module.Product.load
	"""
	td, pd = product_a(test)
	pd.update().store()

	original = (pd.projects, pd.local)
	del pd.projects
	pd.load()

	projects = [
		'/first-context',
		'/second-context',
		'/alt-1',
		'/alt-2',
	]

	for x in projects:
		test/pd.projects << (t_project_id + x)

	test/(pd.projects, pd.local) == original

def test_Product_select(test):
	"""
	# - &module.Product.identifier_by_factor
	# - &module.Product.factor_by_identifier
	"""
	td, pd = product_a(test)
	from ...project import polynomial

	pd.update()
	fp, proto = pd.factor_by_identifier(t_project_id + '/alt-1')
	test/str(fp) == 'ctx.sub.alt-1'
	test/proto == polynomial.V1

	id, proto2 = pd.identifier_by_factor(fp)
	test/proto2 == proto
	test/id == t_project_id + '/alt-1'

def test_Product_image(test):
	"""
	# - &module.Product.image
	"""

	td, pd = product_a(test)
	v = module.types.Variants('SYS', 'ARCH', 'FORM')
	pj = module.types.factor@'ctx.first-context'
	fp = module.types.factor@'factor'

	root = str(pd.route)
	path = '/.images/SYS-ARCH/ctx/first-context/factor.i'
	test/str(pd.image(v, pj, fp)) == (root + path)

def test_Project_no_corpus_part(test):
	"""
	# - &module.Project._iid_corpus_name_pair
	# - &module.Project.corpus
	# - &module.Project.name
	"""
	pj = module.Project.__new__(module.Project)
	pj.identifier = 'no-slash-name'

	test/pj.corpus == ''
	test/pj.name == 'no-slash-name'

def test_Project_corpus_name(test):
	"""
	# - &module.Project._iid_corpus_name_pair
	# - &module.Project.corpus
	# - &module.Project.name
	"""
	pj = module.Project.__new__(module.Project)
	pj.identifier = 'corpus/path/slash-name'

	test/pj.corpus == 'corpus/path'
	test/pj.name == 'slash-name'

def test_Project_select_none(test):
	"""
	# - &module.Project.select
	"""
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	test/str(fp) == 'ctx.sub.alt-1'

	# No factors in alt-1.
	pj = module.Project(pd, t_project_id + '/alt-1', fp, proto({}))
	test/list(pj.select(module.types.factor@"no.such.factor")) == []
	test/list(pj.select(module.types.factor@"")) == []

def test_Project_refer_absolute(test):
	"""
	# - &module.Project.refer
	"""
	F = module.types.factor
	Ref = module.types.Reference
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	test/str(fp) == 'ctx.sub.alt-1'

	pj = module.Project(pd, t_project_id + '/alt-1', fp, proto({}))
	target = t_project_id + '/alt-1'

	test/pj.refer('test') == Ref(target, F@'test')
	test/pj.refer('test.i-validate') == Ref(target, F@'test.i-validate')

def test_Project_refer_relative(test):
	"""
	# - &module.Project.refer
	"""
	F = module.types.factor
	Ref = module.types.Reference
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	test/str(fp) == 'ctx.sub.alt-1'

	target = t_project_id + '/alt-1'
	pj = module.Project(pd, target, fp, proto({}))

	# Default context is project.
	test/pj.refer('.test') == Ref(target, F@'test')
	test/pj.refer('.test', context=F@'subfactor.path') == Ref(target, F@'subfactor.test')
	test/pj.refer('..test', context=F@'subfactor.path') == Ref(target, F@'test')

def test_Project_image_polynomial(test):
	"""
	# - &module.Project.image
	"""
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	pj = module.Project(pd, id, fp, proto({}))

	# No form.
	variants = {
		'system': 'nosys',
		'architecture': 'noarch',
	}

	test_int = pj.image(variants, factor@'test')
	test/test_int.absolute[-4:] == ('alt-1', '__f-int__', 'nosys-noarch', 'test.i')

	subtest_int = pj.image(variants, factor@'path.subtest')
	test/subtest_int.absolute[-4:] == ('path', '__f-int__', 'nosys-noarch', 'subtest.i')

	# With form.
	variants = {
		'system': 'nosys',
		'architecture': 'noarch',
		'form': 'debug'
	}

	test_int = pj.image(variants, factor@'test')
	test/test_int.absolute[-5:] == ('alt-1', '__f-int__', 'nosys-noarch', 'debug', 'test.i')

	subtest_int = pj.image(variants, factor@'path.subtest')
	test/subtest_int.absolute[-5:] == ('path', '__f-int__', 'nosys-noarch', 'debug', 'subtest.i')

def test_Project_extensions(test):
	"""
	# - &module.Project.extensions
	# - &module.Project.icon
	# - &module.Project.synopsis

	# Validate successful extensions.
	"""
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	pj = module.Project(pd, id, fp, proto({}))

	(pj.route@'.project/icon').fs_store(b'data:reference')
	(pj.route@'.project/synopsis').fs_store(b'summary.')
	test/pj.extensions == module.types.Extensions('data:reference', 'summary.')

def test_Project_extensions_vacancies(test):
	"""
	# - &module.Project.extensions
	# - &module.Project.icon
	# - &module.Project.synopsis

	# Validate that exceptions aren't raised by icon and synopsis.
	"""
	td, pd = product_a(test)
	pd.update()
	id = t_project_id + '/alt-1'
	fp, proto = pd.factor_by_identifier(id)
	pj = module.Project(pd, id, fp, proto({}))

	test/pj.extensions == module.types.Extensions(None, None)
	test/pj.icon() == b''
	test/pj.synopsis() == b''

	# Also checking that surrounding whitespace is stripped.
	(pj.route@'.project/icon').fs_store(b'\tdata:reference ')
	del pj.extensions
	test/pj.extensions == module.types.Extensions('data:reference', None)

	(pj.route@'.project/icon').fs_void()
	(pj.route@'.project/synopsis').fs_store(b' summary.\t')
	del pj.extensions
	test/pj.extensions == module.types.Extensions(None, 'summary.')

def test_Context_import_protocol(test):
	"""
	# - &module.Context.import_protocol
	"""
	ctx = module.Context()
	test.issubclass(ctx.import_protocol('factors/polynomial-1'), FactorIsolationProtocol)

def test_Context_connect(test):
	"""
	# - &module.Context.connect
	"""
	td, pd = product_a(test)
	pd.update()
	pd.store()
	ctx = module.Context()

	ctx_pd = ctx.connect(pd.route)
	test/id(pd) != id(ctx_pd)

	# Check cache retrieval.
	test/id(ctx.connect(pd.route)) == id(ctx_pd)

def test_Context_project(test):
	"""
	# - &module.Context.project
	"""
	td, pd = product_a(test)
	pd.update()
	pd.store()
	ctx = module.Context()

	ctx_pd = ctx.connect(pd.route)
	ctx.load()
	test.isinstance(ctx.project(t_project_id + '/alt-1'), module.Project)
	test.isinstance(ctx.project(t_project_id + '/alt-2'), module.Project)

def test_Context_load(test):
	"""
	# - &module.Context.load
	"""
	td, pd = product_a(test)
	pd.update()
	pd.store()

	ctx = module.Context()
	pd = ctx.connect(pd.route)
	ctx.load()

	id = t_project_id + '/alt-1'
	test/(('project', id) in ctx.instance_cache) == True

	id = t_project_id + '/alt-2'
	test/(('project', id) in ctx.instance_cache) == True

def test_project_declaration(test):
	"""
	# - &module.structure_project_declaration
	# - &module.sequence_project_declaration
	"""
	rspd = module.structure_project_declaration
	wspd = module.sequence_project_declaration

	i = Information(
		'http://id.fault.io/corpus/project-name',
		'project-name',
		"Entity Authority",
		"Contact Point",
	)

	t = wspd('factors/void-1', i)
	test/t.endswith("<Contact Point>\n") == True

	pr, ir = rspd(t)
	test/pr == 'factors/void-1'
	test/i == ir
	test/t == wspd(pr, ir)
	test/ir.authority == "Entity Authority"
	test/ir.contact == "Contact Point"

def test_project_declaration_exceptions(test):
	"""
	# - &module.structure_project_declaration
	# - &module.sequence_project_declaration
	"""
	rspd = module.structure_project_declaration
	wspd = module.sequence_project_declaration

	i = Information(
		'http://id.fault.io/corpus/project-name',
		'project-name',
		None, None
	)

	t = wspd('factors/void-1', i)
	pr, ir = rspd(t)

	test/pr == 'factors/void-1'
	test/i == ir
	test/t == wspd(pr, ir)
