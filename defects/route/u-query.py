"""
# Analyze the query module.
"""
from ...route import query as module

def test_iselement(test):
	"""
	# - &module.iselement
	"""
	test/module.iselement(('element', [], {})) == True
	test/module.iselement(('element', [], {'[element]':False})) == False

	test/module.iselement(['element', [], {}]) == True
	test/module.iselement(['element', [], {'[element]':False}]) == False

	test/module.iselement(('element', {})) == False
	test/module.iselement(()) == False
	test/module.iselement(0) == False
	test/module.iselement("") == False
	test/module.iselement("123") == False
	test/module.iselement(True) == False

def test_Context_initialization(test):
	"""
	# - &module.Context.__init__
	"""
	ctx = module.Context(set(), dict())
	ctx = module.Context(set(), dict(), filters={'k': None})
	ctx = module.Context(set(), dict(), filters={'k': None}, identify=(lambda t, n: None))

def test_Context_parse_slice(test):
	"""
	# - &module.Context._parse_slice
	"""
	test/module.Context._parse_slice("1 - 5") == slice(0, 5, 1)
	test/module.Context._parse_slice("1-5") == slice(0, 5, 1)
	test/module.Context._parse_slice("2-5") == slice(1, 5, 1)
	test/module.Context._parse_slice("2") == slice(1, 2, 1)

def test_Context_identify_node(test):
	"""
	# - &module.Context._identify_node
	"""
	t = 'id'
	n = ('type', [], {'identifier': t})
	test/list(module.Context._identify_node(t, n)) == [n]
	test/list(module.Context._identify_node('nothing', n)) == []

def test_Context_prepare_empty(test):
	"""
	# - &module.Context.prepare
	"""
	ctx = module.Context(set(), dict())
	plan = ctx.prepare("")
	test/plan != None

def test_Context_invalid_path(test):
	"""
	# - &module.Context.structure
	# - &module.Context.prepare
	"""
	ctx = module.Context(set(['none', 'alias']), {'a':'alias'})

	# Element type not expressed in context.
	test/module.InvalidPath ^ (lambda: ctx.prepare("/test"))

	# No such filter.
	test/module.InvalidPath ^ (lambda: ctx.prepare("none?notfound"))

	# Invalid slice.
	test/module.InvalidPath ^ (lambda: ctx.prepare("none#meta"))
	test/module.InvalidPath ^ (lambda: ctx.prepare("none# 1- 3"))

	# Multiple selectors present.
	test/module.InvalidPath ^ (lambda: ctx.prepare("*none"))
	test/module.InvalidPath ^ (lambda: ctx.prepare("none*"))

	# With predicate/identifier match.
	test/module.InvalidPath ^ (lambda: ctx.prepare("none[Id]a"))
	test/module.InvalidPath ^ (lambda: ctx.prepare("none[Id]*"))

	# Sanity; valid element types.
	# Ensure that the context is properly configured.
	test/ctx.prepare("/none") != None
	test/ctx.prepare("a") != None

def test_Context_filters(test):
	"""
	# - &module.Context.structure
	# - &module.Context._filter
	"""
	filters = {
		'k': (lambda x: True),
		'j': (lambda x: False),
	}
	ctx = module.Context({'element'}, {'e': 'element'}, filters=filters)
	c = module.Cursor(ctx, [
		('root', [
			('element', [], {'attribute': 0}),
		], {})
	])
	test/c.select("*?k") == [('element', [], {'attribute': 0})]
	test/c.select("*?j") == []
	test/c.select("*?k?j") == []
	test/c.select("*?j?k") == []

def test_Context_all(test):
	"""
	# - &module.Context.structure
	# - &module.Context._all
	"""
	ctx = module.Context({'element'}, {'e': 'element'})

	# Empty
	c = module.Cursor(ctx, [('root', [], {})])
	test/c.select("*") == []

	# One
	c = module.Cursor(ctx, [('root', [('element', [], {})], {})])
	test/c.select("*") == [('element', [], {})]

def test_Context_index(test):
	"""
	# - &module.Context._index
	# - &module.Context.interpret
	"""
	ctx = module.Context({'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [], {'identifier': 'eid-1'}),
			('element', [], {'identifier': 'eid-2'}),
			('element', [], {'identifier': 'eid-3'}),
		], {})
	])

	test/c.select('e#0') == []
	test/c.select('e#1') == [c.root[0][1][0]]
	test/c.select('e#2') == [c.root[0][1][1]]
	test/c.select('e#3') == [c.root[0][1][2]]

	test/c.select('e#1-2') == c.root[0][1][0:2]
	test/c.select('e#2-3') == c.root[0][1][1:3]
	test/c.select('e#1-3') == c.root[0][1][0:3]

	test/c.select('e#1-3#1') == c.root[0][1][0:1]
	test/c.select('e#1-3#2') == c.root[0][1][1:2]

def test_Context_predicate(test):
	"""
	# - &module.Context._predicate
	# - &module.Context.interpret
	"""
	ctx = module.Context({'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [], {'identifier': 'eid-1'}),
			('element', [], {'identifier': 'eid-2'}),
			('element', [], {'identifier': 'eid-3'}),
		], {})
	])

	test/c.select('e[eid-1]') == [c.root[0][1][0]]
	test/c.select('e[eid-2]') == [c.root[0][1][1]]
	test/c.select('e[eid-3]') == [c.root[0][1][2]]

def test_Context_union(test):
	"""
	# - &module.Context._union
	# - &module.Context.interpret
	"""
	ctx = module.Context({'other', 'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [], {'identifier': 'eid-1'}),
			('element', [], {'identifier': 'eid-2'}),
			('other', [], {'identifier': 'eid-3'}),
		], {})
	])

	test/c.select('e|other') == c.root[0][1]
	test/c.select('e[eid-2]|other') == c.root[0][1][1:]
	test/c.select('e[eid-2]|other[eid-3]') == c.root[0][1][1:]
	test/c.select('*#2|other[eid-3]') == c.root[0][1][1:]
	test/c.select('e[eid-1]|e[eid-2]') == c.root[0][1][0:2]

def test_Cursor_select(test):
	"""
	# - &module.Context._select
	# - &module.Cursor.select
	# - &module.Context.switch
	# - &module.Context.interpret
	"""
	ctx = module.Context({'element', 'element.name'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [
				('element', [], {'identifier': 'deep-1'}),
				('element', [], {'identifier': 'deep-2'}),
			], {'attribute': 0}),
			('element', [], {'identifier': 'eid-1'}),
			('element', [], {'identifier': 'eid-2'}),
			('element', [], {'identifier': 'eid-3'}),
		], {})
	])

	test/c.select('element.name') == []
	test/c.select('element') == c.root[0][1]
	test/c.select('element/') == c.root[0][1]
	test/c.select('element#1/element') == c.root[0][1][0][1]
	test/c.select('/element#1/element') == c.root[0][1][0][1]

def test_Cursor_seek(test):
	"""
	# - &module.Cursor.seek
	"""
	ctx = module.Context({'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [
				('element', [], {'identifier': 'deep'}),
			], {'attribute': 0}),
			('element', [], {'identifier': 'eid-1'}),
			('element', [], {'identifier': 'eid-2'}),
			('element', [], {'identifier': 'eid-3'}),
		], {})
	])

	test/c.seek('e#1') == c
	test/c.select('e') == [('element', [], {'identifier': 'deep'})]
	test/c.seek('/e#2') == c
	test/c.select('e') == []

def test_Cursor_reset(test):
	"""
	# - &module.Cursor.reset
	"""
	ctx = module.Context({'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [
				('element', [], {'identifier': 'deep'}),
			], {'attribute': 0}),
			('element', [], {'identifier': 'eid-1'}),
		], {})
	])

	# Avoid directly inspecting .root and ._context_node.
	test/c.seek('e#1') == c
	test/c.select('e') == [('element', [], {'identifier': 'deep'})]
	test/c.reset() == c
	test/c.select('*') == c.root[0][1]

def test_Cursor_fork(test):
	"""
	# - &module.Cursor.fork
	"""
	ctx = module.Context({'element'}, {'e': 'element'})
	c = module.Cursor(ctx, [
		('root', [
			('element', [
				('element', [], {'identifier': 'deep'}),
			], {'attribute': 0}),
			('element', [], {'identifier': 'eid-1'}),
		], {})
	])

	# Avoid directly inspecting .root and ._context_node.
	cc = c.fork('e#1')
	test/cc.select('e') == [('element', [], {'identifier': 'deep'})]
