"""
# Keyword Language Class Parser and Profile tests.
"""
from .. import keywords as module

def mkcsubset(Type):
	# C++ subset used by tests.
	return Type.from_keywords_v1(
		metawords = ['#ifdef', '#if', '#endif', '#pragma'],
		keywords = ['return', 'goto'],
		corewords = ["printf", "scanf"],

		exclusions = [("/*", "*/"), ("//", "")],
		literals = [('"', '"'), ("'", "'")],
		enclosures = [("(", ")")],
		terminators = [";", ","],
		routers = [".", "->", "::"],
		operations = ["+", "-", ">", "<", "--", "++"],
	)

def test_Profile_constructors_v1(test):
	"""
	# - &module.Profile
	"""
	Type = module.Profile

	# Testing effect of improperly created instance.
	x = Type(())
	test/IndexError ^ (lambda: x.metawords)
	test/IndexError ^ (lambda: x.keywords)
	test/IndexError ^ (lambda: x.literals)
	test/IndexError ^ (lambda: x.exclusions)
	test/IndexError ^ (lambda: x.enclosures)
	test/IndexError ^ (lambda: x.routers)
	test/IndexError ^ (lambda: x.terminators)
	test/IndexError ^ (lambda: x.operations)
	test/IndexError ^ (lambda: x.corewords)

	# All fields should be sets.
	emptied = Type.from_keywords_v1()
	test.isinstance(emptied.metawords, set)
	test.isinstance(emptied.keywords, set)
	test.isinstance(emptied.literals, set)
	test.isinstance(emptied.exclusions, set)
	test.isinstance(emptied.enclosures, set)
	test.isinstance(emptied.routers, set)
	test.isinstance(emptied.terminators, set)
	test.isinstance(emptied.operations, set)
	test.isinstance(emptied.corewords, set)

	x = mkcsubset(Type)
	test/(("(", ")") in x.enclosures) == True
	test/(("'", "'") in x.literals) == True
	test/("->" in x.routers) == True

	# Functionality of a Profile instance is
	# tested by &module.Parser tests. An incoherent
	# configuration will eventually lead to an exception.
	ops = list(x.operators)
	test/len(ops) > 0
	test/(('terminator', 'event', ';') in ops) == True

	opclasses = set(x[0] for x in ops)
	test/opclasses == {'terminator', 'enclosure', 'exclusion', 'router', 'operation', 'literal'}

def test_Parser_constructors(test):
	"""
	# - &module.Parser.__init__
	# - &module.Parser.from_profile
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

def test_Parser_words(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	all_types = list(parser.tokenize("#ifdef goto printf"))
	test/all_types[0][0] == 'metaword'
	test/all_types[2][0] == 'keyword'
	test/all_types[4][0] == 'coreword'

	all_types = list(parser.tokenize("#ifdef(goto+printf)"))
	test/all_types[0][0] == 'metaword'
	test/all_types[2][0] == 'keyword'
	test/all_types[4][0] == 'coreword'

	# Boundaries present that are not operators.
	# ")"-padding added to string to allow consistent indexing.
	all_types = list(parser.tokenize("#ifdef_goto_printf))))"))
	test/all_types[0][0] != 'metaword'
	test/all_types[2][0] != 'keyword'
	test/all_types[4][0] != 'coreword'

def test_Parser_exclusion_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	eol_comment = list(parser.tokenize("statement; // EOL"))
	test/eol_comment[-3] == ('exclusion', 'start', '//')

	start_comment = list(parser.tokenize("statement; /* EOL"))
	test/start_comment[-3] == ('exclusion', 'start', '/*')

	stop_comment = list(parser.tokenize("BOL */ statement"))
	test/stop_comment[2] == ('exclusion', 'stop', '*/')

def test_Parser_literal_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	closed_quotation = list(parser.tokenize("statement('quoted string'); // EOL"))
	test/closed_quotation[2] == ('literal', 'delimit', "'")
	test/closed_quotation[6] == ('literal', 'delimit', "'")

	open_quotation = list(parser.tokenize("statement('quoted string); // EOL"))
	test/open_quotation[2] == ('literal', 'delimit', "'")

def test_Parser_enclosure_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	closed_enclosure = list(parser.tokenize("statement('quoted string'); // EOL"))
	test/closed_enclosure[1] == ('enclosure', 'start', "(")
	test/closed_enclosure[7] == ('enclosure', 'stop', ")")

def test_Parser_operation_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	arithmetic = list(parser.tokenize("statement(3+ 2 - 4 +x); // EOL"))
	test/arithmetic[3] == ('operation', 'event', '+')
	test/arithmetic[7] == ('operation', 'event', '-')
	test/arithmetic[11] == ('operation', 'event', '+')
	test/arithmetic[12] == ('identifier', 'event', 'x')
	test/arithmetic[13] == ('enclosure', 'stop', ')')

def test_Parser_router_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	routing = list(parser.tokenize("statement(root->dir.field); // EOL"))
	test/routing[1] == ('enclosure', 'start', '(')
	test/routing[3] == ('router', 'event', '->')
	test/routing[5] == ('router', 'event', '.')

def test_Parser_terminator_classification(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	termination = list(parser.tokenize("statement(p1,p2, p3); // EOL"))
	test/termination[1] == ('enclosure', 'start', '(')
	test/termination[3] == ('terminator', 'event', ',')
	test/termination[5] == ('terminator', 'event', ',')
	test/termination[9] == ('terminator', 'event', ';')

def test_Parser_compound_operators(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	exprs = list(parser.tokenize("x = ++y; // EOL"))
	test/exprs[4] == ('operation', 'event', '++')

def test_Parser_fragments(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	fragment = list(parser.tokenize("x = ++*y; // EOL"))
	test/fragment[4] == ('operation', 'event', '++')

	# This happens due to the absence of "*" in the operations set.
	test/fragment[5] == ('fragment', 'event', '*')

	# This happens due to the absence of "*" in the operations set.
	prefix_fragment = list(parser.tokenize("x = *++y; // EOL"))
	test/prefix_fragment[4] == ('fragment', 'event', '*')
	test/prefix_fragment[5] == ('operation', 'event', '++')

	no_fragment = list(parser.tokenize("x = ++-y; // EOL"))
	# Actual operator identified
	test/no_fragment[5] == ('operation', 'event', '-')

if __name__ == '__main__':
	import sys
	from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
