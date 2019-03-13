from .. import core as library

def test_Point(test):
	p0 = library.Point((0,0))
	p1 = library.Point((1,1))
	p2 = library.Point((2,2))
	p3 = library.Point((5,6))
	test/(p1+p0) == p1
	test/(p1-p0) == p1
	test/(p2-p0) == p2
	test/(p2-p1) == p1
	test/(p2+p1) == (3,3)
	test/(p2+p1) == (3,3)
	test/(p3+p0) == p3
	test/(p3+p1) == (6,7)
	test/(p3-p1) == (4,5)

def test_Position(test):
	"""
	# Check all the methods of &library.Position
	"""
	p = library.Position()
	test/p.snapshot() == (0,0,0)
	test/p.get() == 0

	# checking corner cases
	p.update(2)
	test/p.snapshot() == (0,2,0)

	# above magnitude
	test/p.relation() == 1

	test/p.contract(0, 2)
	test/p.maximum == -2
	test/p.relation() == 1
	test/p.get() == 0 # contract offset was at zero
	test/p.minimum == 0

	p.configure(10, 10, 5)
	test/p.relation() == 0
	test/p.get() == 15
	test/p.maximum == 20
	test/p.minimum == 10

	p.move(5, -1)
	test/p.get() == 15

	p.move(4, -1)
	test/p.get() == 16

	p.move(3, -1)
	test/p.get() == 17

	p.move(0, -1)
	test/p.get() == 20

	p.move(0, 1)
	test/p.get() == 10

	p.move(1, 1)
	test/p.get() == 11

	p.move(1, 0)
	test/p.get() == 12

	p.move(1)
	test/p.get() == 13

	p.update(-1)
	test/p.get() == 12

	p.update(1)
	test/p.get() == 13

	p.update(-4)
	test/p.get() == 9 # before datum
	test/p.relation() == -1

	p.contract(0, 1)
	test/p.relation() == -1
	test/p.get() == 8 # still before datum
	test/p.offset == -2
	test/p.magnitude == 9
	test/p.snapshot() == (10, 8, 19)

def test_Traits(test):
	"""
	# - &library.Traits
	"""

	Traits = library.Traits
	test/Traits.construct('underline').test('underline') == True
	test/Traits.construct('underline').test('double-underline') == False

def test_Traits_unique(test):
	"""
	# - &library.Traits
	"""

	# Given aliases, this will need to change.
	s = set(map(library.Traits.construct, library.Traits.fields))
	test/len(s) == len(library.Traits.fields)

def test_Traits_expected(test):
	"""
	# - &library.Traits
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
	t = library.Traits.construct(*seq)
	seq.sort()
	out = list(t)
	out.sort()
	test/out == seq

def test_RenderParameters(test):
	"""
	# - &library.RenderParameters
	"""

	rp = library.RenderParameters.from_colors(0, 0)
	test/rp.textcolor == 0
	test/rp.cellcolor == 0
	test/rp.traits == 0

	test/rp.update(cellcolor=1) == (0, 1, 0)
	test/rp.update(textcolor=1) == (1, 0, 0)

def test_RenderParameters_from_default(test):
	"""
	# - &library.RenderParameters.from_default
	"""

	# Sanity
	rp = library.RenderParameters.from_default()
	test/rp.textcolor == -1024
	test/rp.cellcolor == -1024
	test/list(rp.traits) == []

def test_RenderParameters_traits(test):
	"""
	# - &library.RenderParameters.clear
	# - &library.RenderParameters.set
	"""

	# Sanity
	rp = library.RenderParameters.from_default()
	ul = library.Traits.construct('underline')
	dul = library.Traits.construct('double-underline')

	rp = rp.set(ul)
	test/list(rp.traits) == ['underline']
	test/list(rp.clear(ul).traits) == []

	rp = rp.set(dul)
	test/list(rp.clear(ul).traits) == ['double-underline']

def test_Phrase_grapheme(test):
	"""
	# - &library.Phrase.grapheme
	"""
	getg = library.Phrase.grapheme
	t = "謝了春\u0353."

	test/t[getg(t, 0)] == t[0]
	test/t[getg(t, 1)] == t[1]
	test/t[getg(t, 4)] == t[-1]

	# Primary checks.
	test/t[getg(t, 2)] == t[2:-1]
	test/t[getg(t, 3)] == t[2:-1]

def test_Phrase_properties(test):
	"""
	# - &library.Phrase.cellcount
	# - &library.Phrase.stringlength
	"""

	ph = library.Phrase.construct([
		("field", None, None, 0)
	])
	test/ph == ((5, "field", (None, None, 0)),)
	test/len(ph) == 1
	test/ph.cellcount() == 5
	test/ph.stringlength() == 5

def test_Phrase_rstripcells_singular(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell
	"""
	ph = library.Phrase.construct([
		("field", None, None, 0)
	])

	result = ph.rstripcells(5)
	test/result == ((0, "", (None, None, 0)),)

	result = ph.rstripcells(4)
	test/result == ((1, "f", (None, None, 0)),)

	result = ph.rstripcells(3)
	test/result == ((2, "fi", (None, None, 0)),)

	result = ph.rstripcells(2)
	test/result == ((3, "fie", (None, None, 0)),)

	result = ph.rstripcells(1)
	test/result == ((4, "fiel", (None, None, 0)),)

	# Validate empty remainder.
	pair = library.Phrase.construct([
		("first", None, None, 0),
		("second", None, None, 0),
	])

	result = pair.rstripcells(6)
	test/result == ((5, "first", (None, None, 0)), (0, '', (None, None, 0)))

def test_Phrase_lstripcells_singular(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell
	"""
	ph = library.Phrase.construct([
		("field", None, None, 0)
	])

	result = ph.lstripcells(1)
	test/result == ((4, "ield", (None, None, 0)),)

	result = ph.lstripcells(2)
	test/result == ((3, "eld", (None, None, 0)),)

	result = ph.lstripcells(3)
	test/result == ((2, "ld", (None, None, 0)),)

	result = ph.lstripcells(4)
	test/result == ((1, "d", (None, None, 0)),)

	result = ph.lstripcells(5)
	test/result == ((0, "", (None, None, 0)),)

	# Validate empty remainder.
	pair = library.Phrase.construct([
		("first", None, None, 0),
		("second", None, None, 0),
	])

	result = pair.lstripcells(5)
	test/result == ((6, "second", (None, None, 0)),)

def test_Phrase_lstripcells_wide(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(1)[0][1] == "*了春"
	test/ph.lstripcells(2)[0][1] == "了春"
	test/ph.lstripcells(3)[0][1] == "*春"
	test/ph.lstripcells(4)[0][1] == "春"
	test/ph.lstripcells(5)[0][1] == "*"
	test/ph.lstripcells(6)[0][1] == ""

def test_Phrase_rstripcells_wide(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",)]
	ph = library.Phrase.construct(seq)
	test/ph.rstripcells(1)[0][1] == "謝了*"
	test/ph.rstripcells(2)[0][1] == "謝了"
	test/ph.rstripcells(3)[0][1] == "謝*"
	test/ph.rstripcells(4)[0][1] == "謝"
	test/ph.rstripcells(5)[0][1] == "*"
	test/ph.rstripcells(6)[0][1] == ""

def test_Phrase_lstripcells_boundary(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",), ("check",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(6)[0][1] != "" # Should not include empty initial.
	test/ph.lstripcells(6)[0][1] == "check"
	test/ph.lstripcells(7)[0][1] == "heck"
	test/IndexError ^ (lambda: ph.lstripcells(7).__getitem__(1))

	seq = [("check",), ("謝了春",),]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(5)[0][1] != "" # Should not include empty initial.
	test/ph.lstripcells(7)[0][1] == "了春"

def test_Phrase_rstripcells_boundary(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("謝了春",), ("check",)]
	ph = library.Phrase.construct(seq)
	test/ph.rstripcells(5)[1][1] == ""
	test/ph.rstripcells(5)[0][1] == "謝了春"
	test/ph.rstripcells(6)[0][1] == "謝了*"
	test/ph.rstripcells(7)[0][1] == "謝了"
	test/IndexError ^ (lambda: ph.rstripcells(7).__getitem__(1))

	iseq = [("check",), ("謝了春",)]
	ph = library.Phrase.construct(iseq)
	test/ph.rstripcells(6)[1][1] == ""
	test/ph.rstripcells(5)[1][1] == "*"
	test/ph.rstripcells(4)[1][1] == "謝"

def test_Phrase_lstripcells_zerowidth(test):
	"""
	# - &library.Phrase.lstripcells
	# - &library.Phrase.lfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	# Zero width space might be greater than zero cells.
	seq = [("Leading, C\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(len("Leading, "))[0][1] == "C\u0353, Following"

	# lfindcell needs to be greedy and consume any zero width characters.
	test/ph.lstripcells(len("Leading, X"))[0][1] == ", Following"

	# Two cells
	seq = [("謝了春\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.lstripcells(6)[0][1] == ", Following"

	noted = []
	def sub(x):
		noted.append(x)
		return '*'
	test/ph.lstripcells(5, substitute=sub)[0][1] == "*, Following"
	test/noted == ["春\u0353"]

def test_Phrase_rstripcells_zerowidth(test):
	"""
	# - &library.Phrase.rstripcells
	# - &library.Phrase.rfindcell

	# Failure is likely due to a malfunctioning &wcswidth implementation.
	"""

	seq = [("Leading, C\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	test/ph.rstripcells(len("Following"))[0][1] == "Leading, C\u0353, "
	test/ph.rstripcells(len(", Following"))[0][1] == "Leading, C\u0353"

	# Unlike lfindcell, zero width is naturally consumed prior to hitting the final offset.
	test/ph.rstripcells(len("x, Following"))[0][1] == "Leading, "

	seq = [("謝了春\u0353, Following",)]
	ph = library.Phrase.construct(seq)
	n = len(", Following")
	test/ph.rstripcells(n)[0][1] == "謝了春\u0353"

	noted = []
	def sub(x):
		noted.append(x)
		return '*'
	test/ph.rstripcells(n+1, substitute=sub)[0][1] == "謝了*"
	test/noted == ["春\u0353"]

def test_Phrase_translate_ascii(test):
	"""
	# - &library.Phrase.translate
	"""

	# one-to-one mapping
	seq = [("first",), ("second",), (" and some more",)]
	ph = library.Phrase.construct(seq)

	for x in range(6):
		test/x == list(ph.translate(x))[0]

	test/list(ph.translate(*range(6))) == list(range(6))

def test_Phrase_translate_empty(test):
	"""
	# - &library.Phrase.translate
	"""

	# empty line
	seq = [("",)]
	ph = library.Phrase.construct(seq)
	xo, = ph.translate(0)
	test/xo == 0
	test/list(ph.translate(1)) == [None]

def test_Phrase_translate_wide(test):
	"""
	# - &library.Phrase.translate
	"""

	seq = [("謝了春謝了春",)]
	ph = library.Phrase.construct(seq)
	for x in range(6):
		xo, = ph.translate(x)
		test/xo == (x*2)

	seq = [("f謝o了春謝了春",)]
	ph = library.Phrase.construct(seq)

	xo, = ph.translate(2)
	test/xo == 3
	xo, = ph.translate(3)
	test/xo == 4
	xo, = ph.translate(4)
	test/xo == 6

def test_Phrase_combine(test):
	"""
	# - &library.Phrase.combine
	"""

	# Zero attributes.
	p = library.Phrase.construct([("prefix",), ("-",), ("suffix",)])
	c = library.Phrase.construct([("prefix-suffix",)])

	test/p.combine() == c

def test_Phrase_subphrase(test):
	"""
	# - &library.Phrase.subphrase
	"""
	seq = [
		("def", 0x0000FF, None, library.Traits(0)),
		(" ", None, None, None),
		("function", None, None, library.Traits(0)),
		("(arguments)", None, None, library.Traits(0)),
		("-> tuple:", None, None, library.Traits(0)),
	]
	ph = library.Phrase.construct(seq)

	# First edge
	test/list(ph.subphrase(*ph.findcells(0, 0))) == [(0, "", ph[0][2])]

	test/list(ph.subphrase(*ph.findcells(0, 3))) == [ph[0]]
	fun = (3, "fun", (None, None, 0))
	test/list(ph.subphrase(*ph.findcells(0, 7))) == [ph[0], ph[1], fun]

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
