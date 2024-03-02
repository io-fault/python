"""
# Validate library defined types and their integration with &..range
"""
import sys
import pickle
from ...syntax import types as module

def test_Address_arithmetic(test):
	a = module.Address((1,0))
	test/a[0] == 1
	test/a[1] == 0

	a = a + 1
	test/a[1] == 1
	a = a - 1
	test/a[1] == 0

def test_Address_from_string(test):
	a = module.Address.from_string('1.5')
	test/a == (1,5)

	a = module.Address.from_string('-1.5')
	test/a == (-1,5)

def test_Address_pickle(test):
	a = module.Address((1,2))
	s = pickle.dumps(a)
	test/a == pickle.loads(s)

def test_Address_string(test):
	a = module.Address((1,2))
	test/str(a) == '1.2'

def test_Address_normalize_stop(test):
	test/module.Address.normalize_stop(0, 1, 1) == (2,0)
	test/module.Address.normalize_stop(1, 1, 1) == (2,0)
	test/module.Address.normalize_stop(1, 31, 1) == (32,0)

	test/module.Address.normalize_stop(33, 31, 1) == (31,1)
	test/module.Address.normalize_stop(33, 31, 33) == (32,0)

	test/module.Address.normalize_stop(33, 35, 33) == (36,0)
	test/module.Address.normalize_stop(33, 35, 32) == (35,32)

def test_Area(test):
	"""
	# Partially redundant with &.module.rangetypes.IRange tests,
	# check the local interface for sanity assurance.
	"""
	a = module.Address((1,5))
	b = module.Address((5,1))
	c = module.Address((10,1))
	A = module.Area((a,b))

	test/(a in A) == True
	test/(b in A) == True
	test/(c in A) == False

def test_Area_string(test):
	a = module.Address((1,2))
	b = module.Address((5,1))
	A = module.Area((a,b))
	test/str(A) == '1.2-5.1'

def test_Area_pickle(test):
	a = module.Address((1,2))
	b = module.Address((5,1))

	A = module.Area((a,b))
	B = pickle.loads(pickle.dumps(A))
	test/A == B

def test_Area_delineate(test):
	a = module.Area.delineate(1,1,5,10,15)
	test/a[0] == (1,1)
	test/a[1] == (5,10)

	b = module.Area.delineate(1,2,5,10,10)
	test/b[0] == (1,2)
	test/b[1] == (6,0)

def test_Area_horizontals(test):
	A = module.Area

	a = A.delineate(1,1,1,16,16)
	test/a.horizontal == False

	b = A.delineate(1,1,1,5,16)
	test/b.horizontal == True

	c = A.delineate(1,1,2,1,23)
	test/c.horizontal == False

sample = [
	"This(1) is the first line.",
	"This(2) is the second line.",
	"",
	"This(3) is the third line.",
	"This(4) is the fourth line.",
]

def test_Area_select(test):
	# Whole single line.
	a = module.Area.delineate(1,1,1,len(sample[0]),len(sample[0]))
	test/a.select(sample) == ('', '', [sample[0]])

	# Exclude initial word.
	a = module.Area.delineate(1,5,1,len(sample[0]),len(sample[0]))
	test/a.select(sample) == ('This', '', ["(1) is the first line."])

	# Exclude initial and final word.
	a = module.Area.delineate(1,5,1,len(sample[0])-5,len(sample[0]))
	test/a.select(sample) == ('This', 'line.', ["(1) is the first "])

	a = module.Area.delineate(1,5,1,len(sample[0])-6,len(sample[0]))
	test/a.select(sample) == ('This', ' line.', ["(1) is the first"])

	# Identical test using second line.
	a = module.Area.delineate(2,5,2,len(sample[1])-6,len(sample[1]))
	test/a.select(sample) == ('This', ' line.', ["(2) is the second"])

	# Odd set of lines with empty.
	a = module.Area.delineate(2,5,4,len(sample[3])-6,len(sample[3]))
	test/a.select(sample) == ('This', ' line.', ["(2) is the second line.", "", "This(3) is the third"])

	# Even set of lines adjacent to end of document.
	a = module.Area.delineate(4,5,5,len(sample[-1])-6,len(sample[-1]))
	test/a.select(sample) == ('This', ' line.', ["(3) is the third line.", "This(4) is the fourth"])

	# Total set
	a = module.Area.delineate(1,1,5,len(sample[-1]),len(sample[-1]))
	test/a.select(sample) == ('', '', sample)
