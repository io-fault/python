"""
# Keyword Language Class Parser and Profile tests.
"""
from ...syntax import keywords as module

def mkcsubset(Type):
	# C++ subset used by tests.
	return Type.from_keywords_v1(
		exclusions = [("/*", "*/"), ("//", "")],
		literals = [('"', '"'), ("'", "'")],
		enclosures = [("(", ")")],
		terminators = [";", ","],
		routers = [".", "->", "::"],
		operations = ["+", "-", ">", "<", "--", "++"],

		# Word types.
		keyword = ['return', 'goto'],
		coreword = ['printf', 'scanf'],
		metaword = ['#ifdef', '#if', '#endif', '#pragma'],
	)

def test_Profile_constructors_v1(test):
	"""
	# - &module.Profile
	"""
	Type = module.Profile

	# Testing effect of improperly created instance.
	x = Type(())
	test/IndexError ^ (lambda: x.words)
	test/IndexError ^ (lambda: x.literals)
	test/IndexError ^ (lambda: x.exclusions)
	test/IndexError ^ (lambda: x.enclosures)
	test/IndexError ^ (lambda: x.routers)
	test/IndexError ^ (lambda: x.terminators)
	test/IndexError ^ (lambda: x.operations)

	# All fields should be sets.
	emptied = Type.from_keywords_v1()
	test.isinstance(emptied.words, dict)
	test.isinstance(emptied.literals, set)
	test.isinstance(emptied.exclusions, set)
	test.isinstance(emptied.enclosures, set)
	test.isinstance(emptied.routers, set)
	test.isinstance(emptied.terminators, set)
	test.isinstance(emptied.operations, set)

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

def test_Parser_spaces(test):
	"""
	# - &module.Parser
	# - &module.Parser.tokenize
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	# Full
	spaced = list(parser.tokenize("\t\tword padding end \t"))
	test/spaced[0] == ('space', 'lead', "\t"*2)
	test/spaced[2] == ('space', 'pad', " "*1)
	test/spaced[4] == ('space', 'pad', " "*1)
	test/spaced[6] == ('space', 'follow', " \t"*1)

	# Follow only
	offset = 0
	spaced = list(parser.tokenize("(word  \t"))
	test/spaced[2] == ('space', 'follow', "  \t"*1)

	# Lead only
	offset = 0
	spaced = list(parser.tokenize("   word)"))
	test/spaced[0] == ('space', 'lead', " "*3)

	# Lead and follow.
	offset = 0
	spaced = list(parser.tokenize("   word\t \n)"))
	test/spaced[0] == ('space', 'lead', " "*3)
	test/spaced[2] == ('space', 'follow', "\t \n"*1)

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

def test_Parser_allocstack(test):
	"""
	# - &module.Parser.allocstack

	# Sanity.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)
	test/parser.allocstack() != None

def test_Parser_delimit_note_nothing(test):
	"""
	# - &module.Parser.delimit

	# Checks that the initial switch is injected in the stream.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	tokens = [
		('identifier', 'event', 'value'),
		('space', 'injection', ' '),
		('identifier', 'event', 'string-data'),
	]

	ctx = parser.allocstack()

	dt = list(parser.delimit(ctx, []))
	test/dt[0] == ('switch', 'inclusion', '')
	test/dt[1:] == []

	dt = list(parser.delimit(ctx, tokens))
	test/dt[0] == ('switch', 'inclusion', '')
	test/dt[1:] == tokens

def test_Parser_delimit_note_exclusion(test):
	"""
	# - &module.Parser.delimit
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	tokens = [
		('exclusion', 'start', '//'),
		('space', 'injection', ' '),
		('identifier', 'event', 'Comment'),
		('space', 'injection', '\n'), # Triggers exit of //
	]

	ctx = parser.allocstack()
	dt = list(parser.delimit(ctx, tokens))

	# Initial state.
	test/dt[0] == ('switch', 'inclusion', '')

	# Exclusion transition
	test/dt[1] == ('switch', 'exclusion', '')

	# Exclusion exit via EOL.
	test/dt[-2] == ('switch', 'inclusion', '')

	# State should be effectively reset.
	test/ctx[-1] == ('inclusion', None)

def test_Parser_delimit_note_capture(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' is transitioned to start and stop.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	tokens = [
		('identifier', 'event', 'value'),
		('space', 'injection', ' '),
		('operation', 'event', '='),
		('space', 'injection', ' '),
		('literal', 'delimit', '"'),
		('identifier', 'event', 'string-data'),
		('literal', 'delimit', '"'), # Triggers exit (stop) of earlier literal.
		('space', 'injection', '\n'),
	]

	ctx = parser.allocstack()
	dt = list(parser.delimit(ctx, tokens))

	# Initial state.
	test/dt[0] == ('switch', 'inclusion', '')

	# Literal transition
	test/dt[5] == ('switch', 'literal', '')

	# Literal exit via delimit.
	test/dt[-2] == ('switch', 'inclusion', '')
	test/dt[-3] == ('literal', 'stop', '"')

	# State should be effectively reset.
	test/ctx[-1] == ('inclusion', None)

# Shared tests for literals and exclusions:

def delimit_nested(test, parser, t_type):
	tokens = [
		('identifier', 'event', 'not-a-comment'),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'first'),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),
		('identifier', 'event', 'third'),
		(t_type, 'stop', '*/'),
		('identifier', 'event', 'not-a-comment'),
		('space', 'injection', '\n'),
	]

	ctx = parser.allocstack()
	dt = list(parser.delimit(ctx, tokens))

	expect = [
		('switch', 'inclusion', ''),
		('identifier', 'event', 'not-a-comment'),

		('switch', t_type, ''),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'first'),

		('switch', t_type, ''),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),

		('switch', t_type, ''),
		('identifier', 'event', 'third'),
		(t_type, 'stop', '*/'),

		('switch', 'inclusion', ''),
		('identifier', 'event', 'not-a-comment'),
		('space', 'injection', '\n'),
	]

	test/dt == expect

def delimit_nested_inconsistent(test, parser, t_type):
	tokens = [
		('identifier', 'event', 'not-a-comment'),
		(t_type, 'start', '//'),
		('identifier', 'event', 'first'),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),
		('identifier', 'event', 'not-a-comment'),
		('space', 'injection', '\n'),
	]

	ctx = parser.allocstack()
	dt = list(parser.delimit(ctx, tokens))

	expect = [
		('switch', 'inclusion', ''),
		('identifier', 'event', 'not-a-comment'),

		('switch', t_type, ''),
		(t_type, 'start', '//'),
		('identifier', 'event', 'first'),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),
		('identifier', 'event', 'not-a-comment'),
		('switch', 'inclusion', ''),
		('space', 'injection', '\n'),
	]

	test/dt == expect
	# Make sure no exclusion state is maintained.
	test/ctx[-1] == ('inclusion', None)

def delimit_nested_inconsistent_alteration(test, parser, t_type):
	tokens = [
		('identifier', 'event', 'not-a-comment'),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'first'),
		(t_type, 'start', '//'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),
		('identifier', 'event', 'not-a-comment'),
		('space', 'injection', '\n'),
	]

	ctx = parser.allocstack()
	dt = list(parser.delimit(ctx, tokens))

	expect = [
		('switch', 'inclusion', ''),
		('identifier', 'event', 'not-a-comment'),

		('switch', t_type, ''),
		(t_type, 'start', '/*'),
		('identifier', 'event', 'first'),
		(t_type, 'start', '//'),
		('identifier', 'event', 'second'),
		(t_type, 'stop', '*/'),

		('switch', 'inclusion', ''),
		('identifier', 'event', 'not-a-comment'),
		('space', 'injection', '\n'),
	]

	test/dt == expect

def test_Parser_delimit_exclusion_nested(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' recognizes nested exclusions with redundant switches.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)
	delimit_nested(test, parser, 'exclusion')

def test_Parser_delimit_exclusion_unnested(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' avoids pushing the context
	# when an inconsistent nested comment is found.
	# "// /* Newline Comment in block */"
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)
	delimit_nested_inconsistent(test, parser, 'exclusion')

def test_Parser_delimit_exclusion_unnested_alternate(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' avoids pushing the context
	# when an inconsistent nested comment is found.
	# "/* // Newline Comment in block */"
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)
	delimit_nested_inconsistent_alteration(test, parser, 'exclusion')

# Identical to the three above, but important to demand consistency 'literal'.

def test_Parser_delimit_literal_nested(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' recognizes nested exclusions with redundant switches.
	"""
	subc = mkcsubset(module.Profile)
	subc.literals.clear()
	subc.literals.update(subc.exclusions)
	subc.exclusions.clear()

	parser = module.Parser.from_profile(subc)
	delimit_nested(test, parser, 'literal')

def test_Parser_delimit_literal_unnested(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' avoids pushing the context
	# when an inconsistent nested comment is found.
	# "// /* Newline Comment in block */"
	"""
	subc = mkcsubset(module.Profile)
	subc.literals.clear()
	subc.literals.update(subc.exclusions)
	subc.exclusions.clear()

	parser = module.Parser.from_profile(subc)
	delimit_nested_inconsistent(test, parser, 'literal')

def test_Parser_delimit_literal_unnested_alternate(test):
	"""
	# - &module.Parser.delimit

	# Checks that 'delimit' avoids pushing the context
	# when an inconsistent nested comment is found.
	# "/* // Newline Comment in block */"
	"""
	subc = mkcsubset(module.Profile)
	subc.literals.clear()
	subc.literals.update(subc.exclusions)
	subc.exclusions.clear()

	parser = module.Parser.from_profile(subc)
	delimit_nested_inconsistent_alteration(test, parser, 'literal')

def test_Parser_process_lines(test):
	"""
	# - &module.Parser.process_lines

	# Sanity check and validation of context breaks.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	first, second = map(list, parser.process_lines(["/* Broken", " * Context */"]))
	dt = first + second

	expect = [
		('switch', 'inclusion', ""),
		('switch', 'exclusion', ""),
		('exclusion', 'start', "/*"),
		('space', 'lead', " "),
		('identifier', 'event', "Broken"),

		('switch', 'inclusion', ""),
		('space', 'follow', " "),
		('fragment', 'event', "*"),
		('space', 'lead', " "),
		('identifier', 'event', "Context"),
		('space', 'follow', " "),
		('exclusion', 'stop', "*/"),
		# It's already at ground state, so this switch does not occur:
		# ('switch', 'inclusion', ""),
	]
	test/dt == expect

def test_Parser_process_document(test):
	"""
	# - &module.Parser.process_document

	# Sanity check and validation of context continuity.
	"""
	subc = mkcsubset(module.Profile)
	parser = module.Parser.from_profile(subc)

	first, second = map(list, parser.process_document(["/* Maintained", " * Context */"]))
	dt = first + second

	expect = [
		('switch', 'inclusion', ""),
		('switch', 'exclusion', ""),
		('exclusion', 'start', "/*"),
		('space', 'lead', " "),
		('identifier', 'event', "Maintained"),

		('switch', 'exclusion', ""),
		('space', 'follow', " "),
		('fragment', 'event', "*"),
		('space', 'lead', " "),
		('identifier', 'event', "Context"),
		('space', 'follow', " "),
		('exclusion', 'stop', "*/"),
		('switch', 'inclusion', ""),
	]
	test/dt == expect
