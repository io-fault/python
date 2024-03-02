from ...context import string as module

def test_normal(test):
	test/module.normal("Nothing happens") == "Nothing happens"
	test/module.normal("One space  trimmed") == "One space trimmed"
	test/module.normal("Two  spaces  trimmed") == "Two spaces trimmed"
	test/module.normal(" Four  spaces  trimmed ") == "Four spaces trimmed"

def test_slug(test):
	test/module.slug("A simple Id") == "A-simple-Id"

	# Surrounding whitespace immune.
	test/module.slug(" A simple Id") == "A-simple-Id"
	test/module.slug(" A simple Id ") == "A-simple-Id"

def test_varsplit(test):
	def split(*args):
		return list(module.varsplit(*args))

	# Maintain split()'s effect when no split occurs.
	test/split('*', "Nothing") == ["Nothing"]

	for x in range(1, 32):
		test/split('*', "Something"+("*"*x)) == ["Something", x, ""]

	for x in range(1, 32):
		test/split('*', "Something"+("*"*x)) == ["Something", x, ""]

	for x in range(1, 32):
		test/split(
			'*', "Something" + ("*"*x) + "Following"
		) == ["Something", x, "Following"]

	for x in range(1, 32):
		test/split(
			'*', "Something" + ("*"*x) + "Following" + ("*"*x)
		) == ["Something", x, "Following", x, '']

def test_ilevel(test):
	for i in range(12):
		test/module.ilevel(i*"\t" + "String.") == i

if __name__ == '__main__':
	from ...test import library as libtest
	import sys; libtest.execute(sys.modules[__name__])
