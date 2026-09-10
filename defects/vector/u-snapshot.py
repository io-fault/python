from ...vector import snapshot as module

def test_structure_empty(test):
	"""
	# - &module.structure
	"""
	test/module.structure("") == ([], "", [])
	test/module.structure(" ") == ([], "", [])

def test_structure_env(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"PATH=/reset\n" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.structure(sample) == ([('PATH', "/reset")], "/bin/cat", ["cat", "/file"])

def test_structure_multiple_env(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"PATH=/reset\n" + \
		"OPTION=data\n" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.structure(sample) == (
		[('PATH', "/reset"), ('OPTION', "data")],
		"/bin/cat", ["cat", "/file"]
	)

def test_structure_no_env(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/file"])

def test_structure_env_unset(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"VAR\n" \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n"

	test/module.structure(sample) == ([('VAR', None)], "/bin/cat", ["cat", "/file"])

def test_structure_newlines(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\n\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/file\n"])

def test_structure_newlines_suffix(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\n suffix\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/file\nsuffix"])

def test_structure_zero_newlines(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\ suffix\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/filesuffix"])

def test_structure_plural_newlines(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\nnn suffix\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/file\n\n\nsuffix"])

def test_structure_no_op(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t|/file\n" + \
		"\t\\\n" + \
		"\t\\\n"

	test/module.structure(sample) == ([], "/bin/cat", ["cat", "/file"])

def test_structure_unknown_qual(test):
	"""
	# - &module.structure
	"""
	sample = "" + \
		"/bin/cat\n" + \
		"\t|cat\n" + \
		"\t?/file\n"

	test/ValueError ^ (lambda: module.structure(sample))

def test_sequence_escapes(test):
	"""
	# - &module.structure
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

	sxp = ''.join(module.sequence(sample))
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

def test_sequence_none(test):
	"""
	# - &module.structure
	"""
	sample = (
		[('ENV', 'env-string'), ('ZERO', None)],
		'/bin/cat',
		[
			"-f", "FILE",
			"\nsuffix",
		]
	)

	sxp = ''.join(module.sequence(sample))
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

def test_structure_space_separated_fields(test):
	"""
	# - &module.structure
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

	test/sample == module.structure(source)
