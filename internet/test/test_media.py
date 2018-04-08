from .. import media as library

def test_module_protocol(test):
	'Type' in test/dir(library)
	'Range' in test/dir(library)

def test_Type(test):
	text_xml = library.Type.from_string('text/xml')
	test/text_xml == library.Type(('text', 'xml', frozenset()))
	test/text_xml.parameters == frozenset()
	text_xml in test/text_xml
	test/str(text_xml) == 'text/xml'
	test/text_xml.pattern == False

	text_xml_options = library.Type.from_string('text/xml;option1;option2')
	test/text_xml_options == library.Type(('text', 'xml', frozenset([('option1',None),('option2',None)])))

	text_any = library.Type.from_string('text/*')
	test/text_any == library.Type(('text', '*', frozenset()))
	test/text_any.parameters == frozenset()
	text_xml in test/text_any
	test/str(text_any) == 'text/*'
	test/text_any.pattern == True

	any_any = library.Type.from_string('*/*')
	test/any_any == library.Type(('*', '*', frozenset()))
	test/any_any.parameters == frozenset()
	text_any in test/any_any
	text_xml in test/any_any
	test/str(any_any) == '*/*'
	test/any_any.pattern == True

	text_html = library.Type.from_string('text/html')
	level1_html = library.Type.from_string('text/html', level='1')
	test/level1_html == level1_html
	test/text_html != level1_html
	level1_html in test/text_html # text_html is the outermost container
	level1_html in test/text_html
	test/str(text_html) == 'text/html'

	# text/html without options is all inclusive,
	# but with options, the containing type must be a subset
	text_html_giraffe = library.Type.from_string('text/html', level='1', giraffe='mr')
	level1_html in test/text_html_giraffe
	text_html_giraffe in test/text_html
	level1_html in test/text_html_giraffe
	txt_set = {'text/html;level=1;giraffe=mr', 'text/html;giraffe=mr;level=1'}
	test/True == (str(text_html_giraffe) in txt_set)

	# Check bytes method.
	test/bytes(text_html) == b'text/html'

def test_Range(test):
	"""
	# Media range queries for managing Accept headers.
	"""
	emptyset = frozenset()

	range = library.Range.from_bytes(b'application/xml,text/xml')
	selection = range.query(library.Type(('text','xml',frozenset([('level','1')]))))
	test/selection == (
		library.Type(('text','xml',frozenset([('level','1')]))),
		library.Type(('text','xml',emptyset)),
		100
	)

	# needs to select /xml over /*
	range = library.Range.from_bytes(b'application/xml,text/*,text/xml')
	selection = range.query(library.Type(('text','xml',frozenset([('level','1')]))))
	test/selection == (
		library.Type(('text','xml',frozenset([('level','1')]))),
		library.Type(('text','xml',emptyset)),
		100
	)

	selection = range.query(library.Type(('text','xml',emptyset)))
	test/selection == (
		library.Type(('text','xml',emptyset)),
		library.Type(('text','xml',emptyset)),
		100
	)

	selection = range.query(library.Type(('text','plain',emptyset)))
	test/selection == (
		library.Type(('text','plain',emptyset)),
		library.Type(('text','*',emptyset)),
		100
	)

	selection = range.query(
		library.Type(('text','plain',emptyset)),
		library.Type(('text','xml',emptyset)),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		library.Type(('text','xml',emptyset)),
		library.Type(('text','xml',emptyset)),
		100
	)

	# some options; give text/xml a lower quality to check text/* matches
	range = library.Range.from_bytes(b'application/xml,text/*;q = 0.5,text/xml')

	selection = range.query(
		library.Type(('text','plain',emptyset)),
		library.Type(('text','xml',emptyset)),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		library.Type(('text','xml',emptyset)),
		library.Type(('text','xml',emptyset)),
		100
	)

	# only query text/plain; should pick up /*
	selection = range.query(
		library.Type(('text','plain',emptyset)),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		library.Type(('text','plain',emptyset)),
		library.Type(('text','*',emptyset)),
		50
	)

	# validate that text/*'s greater quality gives it priority
	range = library.Range.from_bytes(
		b'application/xml;q=0.4,text/*;q = 0.5,text/xml;q=0.2')

	selection = range.query(
		library.Type(('application','xml',emptyset)),
		library.Type(('text','plain',emptyset)),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		library.Type(('text','plain',emptyset)),
		library.Type(('text','*',emptyset)),
		50
	)

	# reveal precedence
	range = library.Range.from_bytes(
		b'text/html,text/html ;  level=\n	1  ,text/*') # whitespace to exercise strip()

	html_l1 = library.Type(('text','html',frozenset([('level','1')])))
	selection = range.query(html_l1)
	# text/html;level=1 should have precedence over text/* and text/html
	test/selection == (html_l1, html_l1, 100)

	# quotes
	range = library.Range.from_string(
		'text/html;foo="me\\h;,\\"",text/xml')

	text_html_foo = library.Type(('text','html',frozenset([('foo','meh;,"')])))
	text_html = library.Type(('text','html',emptyset))
	selection = range.query(text_html)
	# text/html;level=1 should have precedence over text/* and text/html
	test/selection == (text_html, text_html_foo, 100)

def test_file_type(test):
	test/library.file_type('foo.svg') == library.Type.from_string('image/svg+xml')
	test/library.file_type('foo.tar.gz') == library.Type.from_string('application/gzip')
	test/library.file_type('foo.tar') == library.Type.from_string('application/x-tar')
	test/library.file_type('foo.xml') == library.Type.from_string('text/xml')

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
