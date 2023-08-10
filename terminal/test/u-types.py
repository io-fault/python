"""
# - &.types
"""
from .. import types as module
notraits = module.NoTraits
drp = module.RenderParameters.default

def test_Point_interfaces(test):
	"""
	# &module.Point

	# Validate most Point interfaces and arithmetic.
	"""

	P = module.Point

	samples = [
		(0, 0),
		(-5, -5),
		(0, 1),
		(1, 0),
		(-1, 1),
		(1, -1),
	]
	for v in samples:
		V = P(v)
		test/V == v
		test/P.construct(*v) == v
		test/V.x == v[0]
		test/V.y == v[1]
		test.isinstance(-V, P)
		test/-V == (-v[0], -v[1])
		test/(V - (1, 1)) == (v[0] - 1, v[1] - 1)
		test/((2, 3) - V) == (2 - v[0], 3 - v[1])

	p = P((0, 0))
	test/p == (0, 0)
	test/p.x == 0
	test/p.y == 0

	test/p + (1, 2) == (1, 2)
	test.isinstance(p + (1, 2), P)

	test/(1, 2) + p == (1, 2)
	test.isinstance((1, 2) + p, P)

	test/ValueError ^ (lambda: P.construct(1, 2, 3))
	test/ValueError ^ (lambda: P.construct(1,))
	test/ValueError ^ (lambda: P.construct())

def test_Modifiers(test):
	M = module.Modifiers

	m = M(0)
	test/m.control == False
	test/m.shift == False
	test/m.meta == False

	m = M.construct(control=True, meta=True, shift=True)
	test/m.control == True
	test/m.shift == True
	test/m.meta == True

	m = M.construct(control=False, meta=True, shift=False)
	test/m.meta == True
	test/m.control == False
	test/m.shift == False

def test_Traits(test):
	"""
	# - &module.Traits
	"""

	Traits = module.Traits
	test/Traits.construct('underline').test('underline') == True
	test/Traits.construct('underline').test('double-underline') == False
	test/Traits.none() == module.NoTraits

def test_Traits_unique(test):
	"""
	# - &module.Traits
	"""

	# Given aliases, this will need to change.
	s = set(map(module.Traits.construct, module.Traits.fields))
	test/len(s) == len(module.Traits.fields)

def test_Traits_expected(test):
	"""
	# - &module.Traits
	"""
	seq = [
		'underline',
		'double-underline',
		'cross',
		'italic',
		'bold',
		'feint',

		'invisible',
		'inverse',

		'rapid',
		'blink',

		'overline',
		'encircle',
		'frame',
	]

	# Sanity.
	t = module.Traits.construct(*seq)
	seq.sort()
	out = list(t)
	out.sort()
	test/out == seq

def test_RenderParameters(test):
	"""
	# - &module.RenderParameters
	"""

	rp = module.RenderParameters.from_colors(0, 0)
	test/rp.linecolor == -1024
	test/rp.textcolor == 0
	test/rp.cellcolor == 0
	test/rp.traits == 0

	test/rp.update(cellcolor=1) == (0, 0, 1, -1024)
	test/rp.update(textcolor=1) == (0, 1, 0, -1024)
	test/rp.update(linecolor=1) == (0, 0, 0, 1)

def test_RenderParameters_apply(test):
	"""
	# - &module.RenderParamters.apply
	"""
	t = module.NoTraits
	r = module.RenderParameters((t, None, None, None))
	test/r.apply('underline').traits.test('underline') == True
	test/r.apply('underline', 'bold').traits.test('underline') == True
	test/r.apply('underline', 'bold').traits.test('bold') == True

	test/r.apply('bold').textcolor == None
	test/r.apply('bold', textcolor=1).textcolor == 1

def test_RenderParameters_traits(test):
	"""
	# - &module.RenderParameters.clear
	# - &module.RenderParameters.set
	"""

	# Sanity
	rp = module.RenderParameters((module.Traits(0), 0, 0, 0))
	ul = module.Traits.construct('underline')
	dul = module.Traits.construct('double-underline')

	rp = rp.set(ul)
	test/list(rp.traits) == ['underline']
	test/list(rp.clear(ul).traits) == []

	rp = rp.set(dul)
	test/list(rp.clear(ul).traits) == ['double-underline']

def test_RenderParameters_equality(test):
	"""
	# - &module.RenderParameters
	"""
	rp = module.RenderParameters((module.Traits(0), 0, 0, 0))
	rp1 = module.RenderParameters((module.Traits(1), 0, 0, 0))
	rp2 = module.RenderParameters((module.Traits(0), 0, 1, 0))

	test/rp == rp
	test/rp != rp1
	test/rp != rp2

def test_Phrase_properties(test):
	"""
	# - &module.Phrase.cellcount
	# - &module.Phrase.stringlength
	"""

	ph = module.Phrase.construct([
		("field", None, None, 0)
	])
	test/ph == ((5, "field", (None, None, 0)),)
	test/len(ph) == 1
	test/ph.cellcount() == 5
	test/ph.unitcount() == 5

def test_Phrase_combine(test):
	"""
	# - &module.Phrase.combine
	"""

	# Zero attributes.
	p = module.Phrase.construct([("prefix",), ("-",), ("suffix",)])
	c = module.Phrase.construct([("prefix-suffix",)])

	test/p.combine() == c

def test_Phrase_join(test):
	"""
	# - &module.Phrase.join
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	tab = module.Phrase(normal.form("<TAB>"))

	# Three elements.
	r = tab.join([
		normal.form("first"),
		normal.form("middle"),
		normal.form("last"),
	])
	test/''.join([x[1] for x in r]) == "first<TAB>middle<TAB>last"
	test/r[0][2] == normal
	test/r[1] == tab[0]
	test/r[2][2] == normal
	test/r[3] == tab[0]
	test/r[4][2] == normal

	# Two elements.
	r = tab.join([
		normal.form("first"),
		normal.form("last"),
	])
	test/''.join([x[1] for x in r]) == "first<TAB>last"

	# Single element case.
	r = tab.join([
		normal.form("first"),
	])
	test/''.join([x[1] for x in r]) == "first"

	# Zero element case.
	r = tab.join([])
	test/''.join([x[1] for x in r]) == ""

def test_Phrase_seek_forwards(test):
	"""
	# - &module.Phrase.seek

	# Check positive offsets.
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	fields = module.Phrase(map(module.Words, normal.form("field-1", "field-2", "field-3")))
	seek = (lambda x, y: fields.seek(x, y, *module.Phrase.m_codepoint))
	total_len = sum(map(len, (x[1] for x in fields)))

	# Check edges.
	test/fields.seek((0, 0), total_len-1) == ((2, len("field-3")-1), 0)
	test/fields.seek((0, 0), total_len+0) == ((2, len("field-3")), 0)
	test/fields.seek((0, 0), total_len+1) == ((2, len("field-3")), 1)
	test/fields.seek((0, 0), total_len+2) == ((2, len("field-3")), 2)

	# Skip last to avoid zero's next word case.
	for f, w in enumerate(fields):
		l = len(w[1])
		points = [((f, i), l-i) for i in range(l)]

		for p, d in points:
			test/fields.seek(p, d) == ((f, l), 0)

	# Check word edge transition.
	test/fields.seek((0, 0), len(fields[0][1])+0) != ((1, 0), 0)
	test/fields.seek((0, 0), len(fields[0][1])+1) == ((1, 1), 0)
	test/fields.seek((0, 0), len(fields[0][1])+2) == ((1, 2), 0)

def test_Phrase_seek_backwards(test):
	"""
	# - &module.Phrase.seek

	# Check negative offsets.
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	fields = module.Phrase(map(module.Words, normal.form("field-1", "field-2", "field-3")))
	seek = (lambda x, y: fields.seek(x, y, *module.Phrase.m_codepoint))
	total_len = sum(map(len, (x[1] for x in fields)))

	# Check edges.
	test/seek((2, len("field-3")), -(total_len-1)) == ((0, 1), 0)
	test/seek((2, len("field-3")), -(total_len+0)) == ((0, 0), 0)
	test/seek((2, len("field-3")), -(total_len+1)) == ((0, 0), 1)
	test/seek((2, len("field-3")), -(total_len+2)) == ((0, 0), 2)

	for f, w in enumerate(fields):
		l = len(w[1])
		points = [((f, l-i), -(l-i)) for i in range(l)]

		for p, d in points:
			test/seek(p, d) == ((f, 0), 0)

	# Check word edge transition.
	fl = len(fields[1][1])
	test/seek((1, fl), -(fl+0)) != ((0, len(fields[0][1])), 0)
	test/seek((2, 0), -(fl-1)) == ((1, 1), 0)
	test/seek((2, 0), -(fl-2)) == ((1, 2), 0)

def test_Phrase_seek_units(test):
	"""
	# - &module.Phrase.seek

	# Check Character Unit and Character Cell seeks.
	"""
	import itertools
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))

	qfield = module.Phrase(itertools.chain(
		map(module.Words, normal.form('prefix:')),
		map(module.Unit, normal.form('quad')),
		map(module.Words, normal.form(':suffix')),
	))

	test/qfield.seek((0,0), 7, *module.Phrase.m_unit) == ((0, 7), 0)
	test/qfield.seek((0,0), 8, *module.Phrase.m_unit) == ((1, 4), 0)
	test/qfield.seek((0,0), 9, *module.Phrase.m_unit) == ((2, 1), 0)

def test_Phrase_seek_unit_cells(test):
	"""
	# - &module.Phrase.seek

	# Check underflow conditions.
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))

	qfield = module.Phrase([
		module.Unit((4, 'quad', normal)),
	])

	test/qfield.seek((0,0), 1, *module.Phrase.m_cell) == ((0, 0), -1)
	test/qfield.seek((0,0), 2, *module.Phrase.m_cell) == ((0, 0), -2)
	test/qfield.seek((0,0), 3, *module.Phrase.m_cell) == ((0, 0), -3)

	test/qfield.seek((0,4), -1, *module.Phrase.m_cell) == ((0, 0), -3)
	test/qfield.seek((0,4), -2, *module.Phrase.m_cell) == ((0, 0), -2)
	test/qfield.seek((0,4), -3, *module.Phrase.m_cell) == ((0, 0), -1)

def test_Phrase_seek_unit_redirect(test):
	"""
	# - &module.Phrase.seek

	# Validate redirects are identified as a single units.
	"""
	normal = module.RenderParameters((module.Traits(0), -1024, -1024, -1024))

	for rtxt in ['[qw]', '', '22', '1']:
		ph = module.Phrase([
			module.Redirect((len(rtxt), rtxt, normal, '<>')),
		])
		test/ph.unitcount() == 1
		test/ph[0].unitoffset(0) == 0
		test/ph[0].unitoffset(1) == 0
		test/ph[0].unitoffset(2) == 1
		p, r = ph.seek((0, 0), 1, *module.Phrase.m_unit)

		# In this case, one Character Unit needs to map to two Codepoints('<>').
		# The representation text, rtxt, being irrelevant here.
		test/p == (0,2)

def test_Phrase_tell_cells(test):
	"""
	# - &module.Phrase.tell

	# Check cell count accuracy.
	"""
	normal = module.RenderParameters((module.Traits(0), -1024, -1024, -1024))

	qfield = module.Phrase([
		module.Unit((4, 'quad', normal)),
	])
	test/qfield.tell((0,0), *module.Phrase.m_cell) == 0
	test/qfield.tell((0,4), *module.Phrase.m_cell) == 4

	extf = module.Phrase([
		module.Redirect((4, '[qw]', normal, '<>')),
	])
	test/extf.tell((0,0), *module.Phrase.m_cell) == 0
	test/extf.tell((0,2), *module.Phrase.m_cell) == 4

def test_Phrase_fragment_seek(test):
	"""
	# - &module.Phrase.seek

	# Check the effect of seeking to cells in the middle of a Word
	# with a non-single cell usage rate.
	"""

	wc = "中国人"
	p1 = module.Phrase([module.Words((6, wc, drp))])
	for i in range(3):
		co = ((i+1) * 2) - 1
		(wi, cp), r = p1.seek((0, 0), co, *p1.m_cell)
		test/(wi, cp) == (0, i)
		test/r == -1

	# With Redirects now.
	r1 = module.Phrase([module.Redirect((8, ' '*8, drp, '\t'))])
	for i in range(8):
		(wi, cp), r = r1.seek((0, 0), i, *p1.m_cell)
		test/(wi, cp) == (0, 0)
		test/r == -i

def test_Phrase_afirst(test):
	"""
	# - &module.Phrase.afirst
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	fields = module.Phrase(normal.form("field-1", "field-2", "field-3"))
	f1l = len(fields[0][1])

	test/fields.afirst((0, f1l)) == (1, 0)
	test/fields.afirst((1, 0)) == (1, 0)
	test/fields.afirst((1, 1)) == (1, 1)

def test_Phrase_alast(test):
	"""
	# - &module.Phrase.alast
	"""
	normal = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	fields = module.Phrase(normal.form("field-1", "field-2", "field-3"))
	f1l = len(fields[0][1])

	test/fields.alast((0, f1l)) == (0, f1l)
	test/fields.alast((1, 0)) == (0, f1l)
	test/fields.alast((1, 1)) == (1, 1)

def test_Words_split(test):
	"""
	# - &module.Words.split
	"""
	w = module.Words((4, "open", module.RenderParameters((module.NoTraits,))))

	# Middle
	f, l = w.split(2)
	test/f[1] == 'op'
	test/l[1] == 'en'
	test/set([l.style, f.style]) == set([w.style])

	# Front
	f, l = w.split(0)
	test/f[1] == ''
	test/l[1] == 'open'
	test/set([l.style, f.style]) == set([w.style])

	# Back
	f, l = w.split(4)
	test/f[1] == 'open'
	test/l[1] == ''
	test/set([l.style, f.style]) == set([w.style])

def test_Phrase_split(test):
	"""
	# - &module.Phrase.split
	# - &module.Words.split
	"""
	ph = module.Phrase([
		module.Words((4, "open", module.NoTraits)),
		module.Words((5, "close", module.NoTraits)),
	])
	w = (0,0)
	end = (1, 5)
	points = []
	import sys
	for i in range(4+5):
		to, re = ph.seek(w, i)
		test/re == 0
		f, l = ph.split(to)
		test/(f.text + l.text) == "openclose"

def test_Constructors(test):
	"""
	# - &module.RenderParameters.form
	# - &module.Phrase.from_words
	"""
	rp1 = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	rp2 = module.RenderParameters((module.Traits(0), -1024, 0x000000, None))
	test/len(list(rp1.form("first", "second"))) == 2

	ph = module.Phrase.from_words(
		rp1.form("Former", " ", "sentence", ". "),
		rp2.form("Latter sentence", "."),
	)
	test/"".join([x[1] for x in ph]) == "Former sentence. Latter sentence."

	# Check units usage.
	ph = module.Phrase.from_words(
		rp1.form("Former", " ", "sentence", "->"),
		rp2.form("Latter sentence", ";"),
	)
	test/"".join([str(x[1]) for x in ph]) == "Former sentence->Latter sentence;"

def test_Phrase_segment_constructor(test):
	"""
	# - &module.Phrase.from_segmentation
	"""
	rp1 = module.RenderParameters((module.Traits(0), 0xFFFFFF, 0x000000, None))
	rp2 = module.RenderParameters((module.Traits(0), -1024, 0x000000, None))
	ph = module.Phrase.from_segmentation([
		(rp1, [(-4, "four"), (3, "tri")]),
		(rp2, [(4, "word")]),
	])
	test.isinstance(ph[0], module.Unit)
	test.isinstance(ph[1], module.Words)
	test.isinstance(ph[1], module.Words)
	test.isinstance(ph[2], module.Words)
	test/ph[0][2] == rp1
	test/ph[1][2] == rp1
	test/ph[2][2] == rp2
