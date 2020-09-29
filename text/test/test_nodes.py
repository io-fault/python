"""
# Analyze the &.nodes.Cursor implementation.
"""
import sys
from .. import nodes as module

cursor = None
document = \
	"! CONTEXT:\n" \
	"\t/protocol/\n" \
	"\t\t&<http://if.fault.io/test>\n" \
	"[ Section Name ]\n" \
	"First paragraph.\n" \
	"\n" \
	"Second paragraph.\n" \
	"[ Objects ]\n" \
	"# Item1\n" \
	"# Item2\n" \
	"- SetItem1\n" \
	"- SetItem2\n" \
	"\n" \
	"Second paragraph.\n" \
	"[ ] Odd Section [ ]\n" \
	"/key/\n" \
	"\tvalue\n" \
	"[ Final Section ]\n" \
	"Last paragraph.\n" \
	"#!/text parameter-data\n" \
	"\tSubtext Paragraph\n" \
	"\n"

def __test__(test):
	global cursor
	cursor = module.Cursor.from_chapter_text(document)

def test_unrecognized_class(test):
	parse = module.Cursor.prepare
	test/module.PathSyntaxError ^ (lambda: list(parse("/invalid-id")))

def test_unknown_operator(test):
	parse = module.Cursor.prepare
	test/module.PathSyntaxError ^ (lambda: list(parse("/..")))

def test_invalid_selector_single(test):
	parse = module.Cursor.prepare
	test/module.PathSyntaxError ^ (lambda: list(parse("/section[Section Name]paragraph")))

def test_invalid_selector_all(test):
	parse = module.Cursor.prepare
	test/module.PathSyntaxError ^ (lambda: list(parse("/section[Section Name]*")))

def test_no_filter_error(test):
	test/module.ContextMismatch ^ (lambda: cursor.select("/section?no-such-filter"))

def test_select_query_sanity(test):
	r = cursor.select('/section')
	test/len(r) == 4
	ids = [x[-1]['identifier'] for x in r]
	test/ids == ["Section Name", "Objects", "] Odd Section [", "Final Section"]

def test_select_indexing(test):
	test/cursor.select('/section#1')[0][-1]['identifier'] == "Section Name"
	test/cursor.select('/section#2')[0][-1]['identifier'] == "Objects"
	test/cursor.select('/section#3')[0][-1]['identifier'] == "] Odd Section ["
	test/cursor.select('/section#4')[0][-1]['identifier'] == "Final Section"

def test_export_paragraph(test):
	para, = cursor.export("/section[Section Name]/p#1")
	test/para.sole[1] == "First paragraph."

def test_export_syntax(test):
	syntax, = cursor.export("/section#4/syntax#1")
	test/syntax[0] == '/text'
	test/syntax[1] == 'parameter-data'
	test/syntax[2][0] == "Subtext Paragraph"

def test_union(test):
	union, = cursor.select("/section[Objects]/set|sequence")
	test/len(union[1]) == 2

	union, = cursor.select("/section[Objects]/set#1|sequence#1")
	test/len(union[1]) == 2
	union = union[1]
	test/union[0][0] == 'set'
	test/union[1][0] == 'sequence'

def test_filter(test):
	def f(node):
		return node[0] == 'section'
	cursor.filters['test-section'] = f

	for node in cursor.select('/*?test-section'):
		test/node[0] == 'section'

def test_identifier_escapes(test):
	odd, = cursor.select("/section[\\] Odd Section []")
	test/odd[-1]['identifier'] == "] Odd Section ["

if __name__ == '__main__':
	import sys
	from ...test import library as libtest
	libtest.execute(sys.modules['__main__'])
