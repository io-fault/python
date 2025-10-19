from ...range import types as module

def test_combine(test):
	Type = module.IRange
	zero = Type.single(0)
	zero_and_one = Type.normal(0, 1)
	ten = Type.normal(10, 20)

	to_zero = module.combine([ten, Type((0, 9))])
	test/to_zero == [Type((0, 20))]

	# pair generation; near, but not adjacent
	to_zero = module.combine([ten, Type((0, 8))])
	test/to_zero == [Type((0, 8)), Type((10, 20))]

	# pair generation; near, but not adjacent
	to_zero = module.combine([ten, Type((0, 15))])
	test/to_zero == [Type((0, 20))]

def test_IRange(test):
	Type = module.IRange
	zero = Type.single(0)
	zero_and_one = Type.normal(0, 1)
	ten = Type.normal(10, 20)

	test/zero == (0,0)
	test/zero_and_one == (0,1)
	test/ten == (10, 20)

	for x in range(0, 1):
		test/x in zero

	for x in range(0, 2):
		test/x in zero_and_one

	for x in range(10, 21):
		test/x in ten

	test/ten.contiguous(Type((21, 30))) == True
	test/ten.contiguous(Type((0, 9))) == True

	test/ten.contiguous(Type((22, 30))) == False
	test/ten.contiguous(Type((0, 8))) == False

	# exception
	test/list(ten.filter([Type((15, 25))])) == [Type((21, 25))]
	test/list(ten.filter([Type((15, 20))])) == []
	test/list(ten.filter([Type((5, 10))])) == [Type((5, 9))]
	test/list(ten.filter([Type((5, 11))])) == [Type((5, 9))]
	test/list(ten.filter([Type((5, 9))])) == [Type((5, 9))]
	test/list(ten.filter([Type((21, 30))])) == [Type((21, 30))]

def test_IRange_intersect(test):
	Type = module.IRange

	r1 = Type((-10, 10))
	r2 = Type((-5, 5))
	test/list(r1.intersect((r2,))) == [r2]

	r1 = Type((-10, 10))
	r2 = Type((-5, 0))
	test/list(r1.intersect((r2,))) == [r2]

	r1 = Type((-10, 10))
	r2 = Type((-15, -5))
	test/list(r1.intersect((r2,))) == [Type((-10, -5))]

	r1 = Type((-10, 10))
	r2 = Type((5, 15))
	test/list(r1.intersect((r2,))) == [Type((5, 10))]

	# no intersection
	r1 = Type((-10, 10))
	r2 = Type((11, 15))
	test/list(r1.intersect((r2,))) == []

	# one unit of intersection
	r1 = Type((-10, 10))
	r2 = Type((10, 15))
	test/list(r1.intersect((r2,))) == [Type((10, 10))]

def test_Set(test):
	FType = module.IRange
	Type = module.Set

	rs = Type.from_normal_sequence([FType((0, 5000))])
	test/list(rs) == [FType((0, 5000))]
	test/rs.__contains__(50) == True

	# Remove and test effects.
	rs.discard(FType((0, 10)))
	test/rs.__contains__(0) == False
	test/rs.__contains__(5) == False
	test/rs.__contains__(50) == True
	test/rs.__contains__(50) == True
	rs.discard(FType((50,50)))
	test/rs.__contains__(50) == False

	for x in range(10):
		test/rs.__contains__(x) == False

	test/rs.__contains__(6000) == False
	rs.add(FType((6000, 6500)))
	test/rs.__contains__(6000) == True
	test/rs.__contains__(6300) == True
	test/rs.__contains__(6001) == True
	test/rs.__contains__(6501) == False
	test/rs.__contains__(6000-1) == False

	rs = Type.from_string('123 321 400-420 450-1000 4320-5000')
	test/rs.__contains__(123) == True
	test/rs.__contains__(6000) == False
	test/rs.__contains__(124) == False
	test/rs.__contains__(600) == True

	rs.discard(FType((100, 400)))
	test/rs.__contains__(123) == False
	test/rs.__contains__(400) == False

def test_Set_difference(test):
	FType = module.IRange
	Type = module.Set

	rs1 = Type.from_string('123 321 400-420 450-1000 4320-5001')
	rs2 = Type.from_string('321 400-420 600-800 4320-5000')
	d = rs1 - rs2

	test/str(d) == '123 450-599 801-1000 5001'

def test_Set_intersection(test):
	FType = module.IRange
	Type = module.Set

	rs1 = Type.from_string('123 321 400-600 702 750')
	rs2 = Type.from_string('124-130 450-500 700-800')
	d = rs1.intersection(rs2)
	d = Type.from_normal_sequence(list(d))

	test/list(d.intersecting(FType((450,500)))) != []

def test_Set_union(test):
	FType = module.IRange
	Type = module.Set

	rs1 = Type.from_string('123-321 400-600 702 750')
	rs2 = Type.from_string('700-800 900-950')
	test/str(rs1.union(rs2)) == '123-321 400-600 700-800 900-950'

def test_Set_len(test):
	FType = module.IRange
	Type = module.Set

	rs = Type.from_string('100-200 400-500 1000-5000')
	test/len(rs) == (101 + 101 + 4001)

	rs = Type.from_string('0 2 4 6 100-200 400-500 1000-5000')
	test/len(rs) == (101 + 101 + 4001 + 4)

	rs = Type.from_string('')
	test/len(rs) == 0

	rs = Type.from_string('1')
	test/len(rs) == 1

def test_Set_pickle(test):
	import pickle
	Type = module.Set
	original = Type.from_string('100-200 500-1000')
	binary = pickle.dumps(original)
	restored = pickle.loads(binary)
	test/restored == original

def test_Mapping_narrow_indexing(test):
	"""
	# - &module.Mapping.__setitem__
	# - &module.Mapping.__getitem__

	# Check single level siblings access.
	"""
	Type = module.Mapping
	i = Type(-1)
	k1 = module.IRange.from_string('100-500')
	k2 = module.IRange.from_string('600-700')

	i[k1] = 'first'
	i[k2] = 'second'
	test/i[k1] == 'first'
	test/i[k2] == 'second'
	test/i[module.IRange.from_string('200-300')] == 'first'
	test/i[module.IRange.from_string('650-675')] == 'second'

def test_Mapping_get(test):
	"""
	# - &module.Mapping.__setitem__
	# - &module.Mapping.get

	# Check single level siblings access.
	"""
	Type = module.Mapping
	i = Type(-1)
	k1 = module.IRange.from_string('100-500')
	k2 = module.IRange.from_string('505-600')
	test/i.get(k1) == None
	test/i.get(k1, default=None) == None

	i[k1] = 'first'
	test/i.get(k1) == 'first'
	test/i.get(k2) == None

def test_Mapping_depth_indexing(test):
	"""
	# - &module.Mapping.__getitem__
	# - &module.Mapping.__setitem__

	# Check that inner values set after override initial values.
	"""

	Type = module.Mapping
	i = Type(-1)
	IR = module.IRange.from_string
	k1 = IR('100-500')
	k2 = IR('300-400')

	i[k1] = 'first'
	test/i[k1] == 'first'
	i[k2] = 'second'
	test/i[k2] == 'second'

	test/i[IR('100-299')] == 'first'
	test/i[IR('110-150')] == 'first'
	test/i[IR('450-490')] == 'first'
	test/i[IR('299')] == 'first'
	test/i[IR('401')] == 'first'

	test/i[IR('330-360')] == 'second'
	test/i[IR('300')] == 'second'
	test/i[IR('400')] == 'second'

def test_Mapping_path(test):
	"""
	# - &module.Mapping.path

	# Check the effect of stacked ranges on path.
	"""

	Type = module.Mapping
	i = Type(-1)
	IR = module.IRange.from_string

	k1 = IR('100-500')
	k2 = IR('300-400')
	k3 = IR('350-360')

	test/[x[1] for x in i.path(k1)] == []

	i[k1] = 'first'
	test/[x[1] for x in i.path(k2)] == ['first']

	i[k2] = 'second'
	test/[x[1] for x in i.path(k1)] == ['first', 'second']
	test/[x[1] for x in i.path(k2)] == ['first', 'second']

	i[k3] = 'third'
	test/[x[1] for x in i.path(k3)] == ['first', 'second', 'third']
	test/[x[1] for x in i.path(k2)] == ['first', 'second', 'third']
	test/[x[1] for x in i.path(k1)] == ['first', 'second', 'third']

def test_Mapping_kv_query(test):
	"""
	# - &module.Mapping.keys
	# - &module.Mapping.values
	# - &module.Mapping.items
	"""

	Type = module.Mapping
	i = Type(-1)
	IR = module.IRange.from_string
	k1 = IR('100-500')
	k2 = IR('300-400')
	k3 = IR('350-360')

	test/list(i.keys()) == []
	test/list(i.values()) == []

	i[k1] = 'first'
	i[k2] = 'second'
	test/list(i.keys()) == [k1, k2]
	test/list(i.values()) == ['first', 'second']

	i[k3] = 'third'
	test/list(i.values()) == ['first', 'second', 'third']
	test/list(i.keys()) == [k1, k2, k3]

	test/list(i.items()) == [(k1, 'first'), (k2, 'second'), (k3, 'third')]

def test_Mapping_update(test):
	"""
	# - &module.Mapping.update
	# - &module.Mapping.items
	"""
	Type = module.Mapping
	i = Type(-1)
	i2 = Type(-2)
	k1 = module.IRange.from_string('100-500')
	k2 = module.IRange.from_string('300-400')
	k3 = module.IRange.from_string('350-360')

	i.update([
		(k1, 'first'),
	])
	test/list(i.items()) == [(k1, 'first')]
	i2.update([
		(k2, 'second')
	])

	i.update(i2)
	test/list(i.items()) == [(k1, 'first'), (k2, 'second')]
