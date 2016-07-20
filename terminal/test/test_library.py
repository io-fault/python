from .. import library

def test_Position(test):
	"""
	Check &library.Position
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

def test_offsets(test):
	"""
	Check the character width analysis.
	"""

	# one-to-one mapping
	seq = [("first",), ("second",), (" and some more",)]
	for x in range(6):
		test/x == list(library.offsets(seq, x))[0]

	test/list(library.offsets(seq, *range(6))) == list(range(6))

	# empty line
	seq = [("",)]
	xo, = library.offsets(seq, 0)
	test/xo == 0

	test/IndexError ^ library.offsets(seq, 1).__next__

	# wide characters
	seq = [("林花謝了春紅",)]
	for x in range(6):
		xo, = library.offsets(seq, x)
		test/xo == (x*2)

	seq = [("f林o花謝了春紅",)]
	xo, = library.offsets(seq, 2)
	test/xo == 3
	xo, = library.offsets(seq, 3)
	test/xo == 4
	xo, = library.offsets(seq, 4)
	test/xo == 6

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules[__name__])
