"""
# Validate the format module's functionality.
"""
from ...syntax import format as module

def test_Fields_operations(test):
	"""
	# - &module.Fields
	"""

	f = module.Fields(',', (lambda x, y: (('T', v.strip()) for v in y.split(x))))
	f.separation == ','

	src = 'first, second , third ' # Spaces intended.
	types = ['T'] * 3
	values = ['first', 'second', 'third']
	test/list(f.structure([src])) == [list(zip(types, values))]
	test/next(f.sequence(f.structure([src]))) == 'firstsecondthird'

def test_Fields_partial(test):
	"""
	# - &module.Fields.partial
	"""

	def fsplit(sep, ln, k=''):
		for v in ln.split(sep):
			yield ('T', k+v.strip())

	f = module.Fields(',', fsplit)
	cf = f.partial()
	types = 'TTT'
	test/list(cf("1,2,3")) == list(zip(types, ["1", "2", "3"]))

	cf = f.partial(k='p-')
	test/list(cf("1,2,3")) == list(zip(types, ["p-1", "p-2", "p-3"]))

def test_Lines_defaults(test):
	"""
	# - &module.Lines
	"""

	t = module.Lines()
	test/t.termination == "\n"
	test/t.indentation == "\t"

def test_partial_termination(test):
	"""
	# - &module.Lines.measure_partial_termination
	"""

	t = module.Lines("\r\n")
	test/t.measure_partial_termination("sol") == 0
	test/t.measure_partial_termination("sol\r") == 1

	# Full matches aren't checked.
	test/t.measure_partial_termination("sol\r\n") == 0

	# Check unusual boundary.
	t = module.Lines("\x00\x01\x02")
	test/t.measure_partial_termination("sol\x00") == 1
	test/t.measure_partial_termination("sol\x00\x01") == 2
	test/t.measure_partial_termination("sol\x01\x02") == 0

def test_Lines_splitpartial(test):
	"""
	# - &module.Lines._splitpartial
	"""

	t = module.Lines()
	test/t._splitpartial("\n", "a\nb") == ("b", ["a"])
	test/t._splitpartial("\n", "a\nb", "l") == ("b", ["la"])

	# No termination.
	test/t._splitpartial("\n", "a") == ("a", [])

def test_Lines_splitpartial_plural(test):
	"""
	# - &module.Lines._splitpartial
	"""

	t = module.Lines("\n\n")
	test/t._splitpartial("\n\n", "a\n\nb") == ("b", ["a"])
	test/t._splitpartial("\n\n", "a\n\nb", "l") == ("b", ["la"])
	test/t._splitpartial("\n\n", "a\n\nb\n\n", "l") == ("", ["la", "b"])

	# No termination.
	test/t._splitpartial("\n\n", "a") == ("a", [])

def test_Lines_measure_indentation(test):
	"""
	# - &module.Lines.measure_indentation
	"""

	samples = ["\t", " "*2, " "*4]

	for ilc in samples:
		t = module.Lines("\n", ilc)
		test/t.indentation == ilc

		for i in range(10):
			test/t.measure_indentation((i * t.indentation) + "content") == i

def test_Lines_level(test):
	"""
	# - &module.Lines.level
	"""

	samples = ["\t", " "*2, " "*4]

	for ilc in samples:
		t = module.Lines("\n", ilc)
		test/t.indentation == ilc

		for i in range(10):
			test/t.level((i * t.indentation) + "content") == (i, "content")

def test_Lines_structure(test):
	"""
	# - &module.Lines.structure
	"""

	t = module.Lines()

	# Empty iterable, empty line sequence.
	test/list(t.structure([])) == []
	test/list(t.structure([""])) == []
	test/list(t.structure(["", ""])) == []

	# Single line; no termination.
	test/list(t.structure(["text"])) == [(0, "text")]
	test/list(t.structure(["text\n"])) == [(0, "text")]
	test/list(t.structure(["t", "ext"])) == [(0, "text")]
	test/list(t.structure(["te", "xt"])) == [(0, "text")]
	test/list(t.structure(["tex", "t"])) == [(0, "text")]
	test/list(t.structure(["t", "e", "x", "t"])) == [(0, "text")]
	test/list(t.structure(["te", "", "", "xt"])) == [(0, "text")]

	sample = "first\nsecond\n\tthird\n\tfourth"
	test/list(t.structure([sample])) == [
		(0, "first"),
		(0, "second"),
		(1, "third"),
		(1, "fourth"),
	]

def progression(test, ft, limit):
	ilc = ft.indentation
	lsc = ft.termination

	expect = [(i, str(i)) for i in range(limit)]
	sample = ''.join((i * ilc) + str(i) + lsc for i in range(limit))
	test/list(ft._splitpartial(ft.termination, sample)) == \
		list(('', [(i*ilc) + lc for i, lc in expect]))

	for fs in range(1, 8):
		fragments = [sample[i:i+fs] for i in range(0, len(sample), fs)]
		test/list(ft.structure(fragments)) == expect

def test_Lines_progression_spaces(test):
	"""
	# - &module.Lines.structure
	"""

	for i in range(1, 6):
		t = module.Lines('\n', ' '*i)
		progression(test, t, 45)

def test_Lines_progression_tabs(test):
	"""
	# - &module.Lines.structure
	"""

	progression(test, module.Lines('\r\n'), 45)
	progression(test, module.Lines(), 45)

def test_Lines_sequence(test):
	"""
	# - &module.Lines.sequence
	"""

	lnfmt = module.Lines()
	test/''.join(lnfmt.sequence([(1, 'content')])) == '\tcontent\n'

def test_Characters_from_codec(test):
	"""
	# - &module.Characters.from_codec
	"""

	from_codec = module.Characters.from_codec
	cufmt_strict = from_codec('utf-8', 'strict')
	cufmt = from_codec('utf-8', 'surrogateescape')

	b = b'\xFF\xFF\xFF\x00'
	t = cufmt.decode(b)
	test/cufmt.encode(t) == b

	test/UnicodeDecodeError ^ (lambda: cufmt_strict.decode(b))
	test/UnicodeEncodeError ^ (lambda: cufmt_strict.encode(t))
	test/UnicodeDecodeError ^ (lambda: list(cufmt_strict.structure([b])))
	test/UnicodeEncodeError ^ (lambda: list(cufmt_strict.sequence([t])))

def test_Characters_structure(test):
	"""
	# - &module.Characters.structure
	"""

	cu = module.Characters.from_codec('utf-8', 'surrogateescape')
	test/list(cu.structure([b'utf-8 data'])) == ['utf-8 data', '']

text_samples = [
	"test",
	"测试",
	b'\xFF\xFF\xFF\x00'.decode('utf-8', 'surrogateescape'),
	"",
]

def test_Characters_io_fragments(test):
	"""
	# - &module.Characters.structure
	# - &module.Characters.sequence
	"""

	cu = module.Characters.from_codec('utf-8', 'surrogateescape')
	for sample in text_samples:
		expect = sample.encode('utf-8', 'surrogateescape')
		idata = (expect[i:i+1] for i in range(len(expect)))
		test/b''.join(cu.sequence(cu.structure(idata))) == expect
