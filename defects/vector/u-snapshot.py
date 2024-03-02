from ...vector import snapshot as module

def test_parse_empty(test):
	"""
	# - &module.parse
	"""
	test/module.parse("") == ([], "", [])
	test/module.parse(" ") == ([], "", [])

def test_parse_env(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"PATH=/reset\n" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.parse(sample) == ([('PATH', "/reset")], "/bin/cat", ["cat", "/file"])

def test_parse_multiple_env(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"PATH=/reset\n" + \
		"OPTION=data\n" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.parse(sample) == (
		[('PATH', "/reset"), ('OPTION', "data")],
		"/bin/cat", ["cat", "/file"]
	)

def test_parse_no_env(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/file"])

def test_parse_env_unset(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"VAR\n" \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.parse(sample) == ([('VAR', None)], "/bin/cat", ["cat", "/file"])

def test_parse_newlines(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\n\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/file\n"])

def test_parse_newlines_suffix(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\n suffix\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/file\nsuffix"])

def test_parse_zero_newlines(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\ suffix\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/filesuffix"])

def test_parse_plural_newlines(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\nnn suffix\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/file\n\n\nsuffix"])

def test_parse_no_op(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\\n" + \
		"\t\\\n"

	test/module.parse(sample) == ([], "/bin/cat", ["cat", "/file"])

def test_parse_unknown_qual(test):
	"""
	# - &module.parse
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t?/file\n"

	test/ValueError ^ (lambda: module.parse(sample))

def test_serialize_escapes(test):
	"""
	# - &module.parse
	"""
	sample = (
		[('ENV', 'env-string')],
		'/bin/cat',
		[
			"-f", "FILE",
			"",
			"\nsuffix",
		]
	)

	sxp = ''.join(module.serialize(sample))
	test/sxp.split('\n') == [
		"ENV=env-string",
		"/bin/cat",
		"\t|-f",
		"\t|FILE",
		"\t|",
		"\t|",
		"\t\\n suffix",
		"",
	]

def test_serialize_none(test):
	"""
	# - &module.parse
	"""
	sample = (
		[('ENV', 'env-string'), ('ZERO', None)],
		'/bin/cat',
		[
			"-f", "FILE",
			"\nsuffix",
		]
	)

	sxp = ''.join(module.serialize(sample))
	test/sxp.split('\n') == [
		"ENV=env-string",
		"ZERO",
		"/bin/cat",
		"\t|-f",
		"\t|FILE",
		"\t|",
		"\t\\n suffix",
		"",
	]

def test_parse_space_separated_fields(test):
	"""
	# - &module.parse
	"""
	sample = (
		[('ENV', 'env-string'), ('ZERO', None)],
		'/bin/cat',
		[
			"-f", "FILE",
			"-n", "NUMBER",
			"captured spaces   ",
			"-ab", "-cde" + "\nsuffix",
		]
	)

	source = '\n'.join([
		"ENV=env-string",
		"ZERO",
		"/bin/cat",
		"\t: -f FILE -n NUMBER  ",
		"\t|captured spaces   ",
		"\t: -ab -cde",
		"\t\\n suffix",
		"",
	])

	test/sample == module.parse(source)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
