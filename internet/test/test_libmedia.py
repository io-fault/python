from .. import libmedia

def test_module_protocol(test):
	'Type' in test/dir(libmedia)
	'Range' in test/dir(libmedia)

def test_Type(test):
	# this tests .parse_accept and .parse_options
	text_xml = libmedia.Type.from_string('text/xml')
	test/text_xml == libmedia.Type(('text', 'xml', frozenset()))
	test/text_xml.parameters == frozenset()
	text_xml in test/text_xml

	text_any = libmedia.Type.from_string('text/*')
	test/text_any == libmedia.Type(('text', '*', frozenset()))
	test/text_any.parameters == frozenset()
	text_xml in test/text_any

	any_any = libmedia.Type.from_string('*/*')
	test/any_any == libmedia.Type(('*', '*', frozenset()))
	test/any_any.parameters == frozenset()
	text_any in test/any_any
	text_xml in test/any_any

	text_html = libmedia.Type.from_string('text/html')
	level1_html = libmedia.Type.from_string('text/html', level='1')
	test/level1_html == level1_html
	test/text_html != level1_html
	level1_html in test/text_html # text_html is the outermost container
	level1_html in test/text_html

	# text/html without options is all inclusive,
	# but with options, the containing type must be a subset
	text_html_giraffe = libmedia.Type.from_string('text/html', level='1', giraffe='mr')
	level1_html in test/text_html_giraffe
	text_html_giraffe in test/text_html
	level1_html in test/text_html_giraffe

def test_Range(test):
	'media range of accept header'
	range = libmedia.Range.from_bytes(b'application/xml,text/xml')
	selection = range.query(libmedia.Type(('text','xml',frozenset(('level','1')))))
	test/selection == (
		libmedia.Type(('text','xml',frozenset(('level','1')))),
		libmedia.Type(('text','xml',frozenset())),
		100
	)

	# needs to select /xml over /*
	range = libmedia.Range.from_bytes(b'application/xml,text/*,text/xml')
	selection = range.query(libmedia.Type(('text','xml',frozenset(('level','1')))))
	test/selection == (
		libmedia.Type(('text','xml',frozenset(('level','1')))),
		libmedia.Type(('text','xml',frozenset())),
		100
	)

	selection = range.query(libmedia.Type(('text','xml',frozenset())))
	test/selection == (
		libmedia.Type(('text','xml',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
		100
	)

	selection = range.query(libmedia.Type(('text','plain',frozenset())))
	test/selection == (
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','*',frozenset())),
		100
	)

	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		libmedia.Type(('text','xml',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
		100
	)

	# some options; give text/xml a lower quality to check text/* matches
	range = libmedia.Range.from_bytes(b'application/xml,text/*;q = 0.5,text/xml')

	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		libmedia.Type(('text','xml',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
		100
	)

	# only query text/plain; should pick up /*
	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','*',frozenset())),
		50
	)

	# validate that text/*'s greater quality gives it priority
	range = libmedia.Range.from_bytes(
		b'application/xml;q=0.4,text/*;q = 0.5,text/xml;q=0.2')

	selection = range.query(
		libmedia.Type(('application','xml',frozenset())),
		libmedia.Type(('text','plain',frozenset())),
	)
	# text/xml should have precedence over text/*
	test/selection == (
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','*',frozenset())),
		50
	)

	# reveal precedence
	range = libmedia.Range.from_bytes(
		b'text/html,text/html ;  level=\n	1  ,text/*') # whitespace to exercise strip()

	html_l1 = libmedia.Type(('text','html',frozenset([('level','1')])))
	selection = range.query(html_l1)
	# text/html;level=1 should have precedence over text/* and text/html
	test/selection == (html_l1, html_l1, 100)

	# quotes
	range = libmedia.Range.from_string(
		'text/html;foo="me\\h;,\\"",text/xml')

	text_html_foo = libmedia.Type(('text','html',frozenset([('foo','meh;,"')])))
	text_html = libmedia.Type(('text','html',frozenset()))
	selection = range.query(text_html)
	# text/html;level=1 should have precedence over text/* and text/html
	test/selection == (text_html, text_html_foo, 100)

if __name__ == '__main__':
	import sys; from ...development import libtest
	libtest.execute(sys.modules['__name__'])
