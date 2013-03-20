from .. import libmedia

# Sanity
def test_module_protocol(test):
	test.fail_if_not_hasattr(libmedia, 'Type')
	test.fail_if_not_hasattr(libmedia, 'Range')

def test_Type(test):
	# this tests .parse_accept and .parse_options
	text_xml = libmedia.Type.from_string('text/xml')
	test.fail_if_not_equal(text_xml, libmedia.Type(('text', 'xml', frozenset())))
	test.fail_if_not_equal(text_xml.options, frozenset())
	test.fail_if_not_in(text_xml, text_xml)

	text_any = libmedia.Type.from_string('text/*')
	test.fail_if_not_equal(text_any, libmedia.Type(('text', '*', frozenset())))
	test.fail_if_not_equal(text_any.options, frozenset())
	test.fail_if_not_in(text_xml, text_any)

	any_any = libmedia.Type.from_string('*/*')
	test.fail_if_not_equal(any_any, libmedia.Type(('*', '*', frozenset())))
	test.fail_if_not_equal(any_any.options, frozenset())
	test.fail_if_not_in(text_any, any_any)
	test.fail_if_not_in(text_xml, any_any)

	text_html = libmedia.Type.from_string('text/html')
	level1_html = libmedia.Type.from_string('text/html', level='1')
	test.fail_if_not_equal(level1_html, level1_html)
	test.fail_if_equal(text_html, level1_html)
	test.fail_if_in(text_html, level1_html) # text_html is the outermost container
	test.fail_if_not_in(level1_html, text_html)

	# text/html without options is all inclusive,
	# but with options, the containing type must be a subset
	text_html_giraffe = libmedia.Type.from_string('text/html', level='1', giraffe='mr')
	test.fail_if_in(text_html_giraffe, level1_html)
	test.fail_if_not_in(text_html_giraffe, text_html)
	test.fail_if_not_in(level1_html, text_html_giraffe)

def test_Range(test):
	'media range of accept header'
	range = libmedia.Range.from_bytes(b'application/xml,text/xml')
	selection = range.query(libmedia.Type(('text','xml',frozenset(('level','1')))))
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','xml',frozenset(('level','1')))),
			libmedia.Type(('text','xml',frozenset())),
			100
		)
	)

	# needs to select /xml over /*
	range = libmedia.Range.from_bytes(b'application/xml,text/*,text/xml')
	selection = range.query(libmedia.Type(('text','xml',frozenset(('level','1')))))
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','xml',frozenset(('level','1')))),
			libmedia.Type(('text','xml',frozenset())),
			100
		)
	)

	selection = range.query(libmedia.Type(('text','xml',frozenset())))
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','xml',frozenset())),
			libmedia.Type(('text','xml',frozenset())),
			100
		)
	)

	selection = range.query(libmedia.Type(('text','plain',frozenset())))
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','plain',frozenset())),
			libmedia.Type(('text','*',frozenset())),
			100
		)
	)

	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
	)
	# text/xml should have precedence over text/*
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','xml',frozenset())),
			libmedia.Type(('text','xml',frozenset())),
			100
		)
	)

	# some options; give text/xml a lower quality to check text/* matches
	range = libmedia.Range.from_bytes(b'application/xml,text/*;q = 0.5,text/xml')

	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
		libmedia.Type(('text','xml',frozenset())),
	)
	# text/xml should have precedence over text/*
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','xml',frozenset())),
			libmedia.Type(('text','xml',frozenset())),
			100
		)
	)

	# only query text/plain; should pick up /*
	selection = range.query(
		libmedia.Type(('text','plain',frozenset())),
	)
	# text/xml should have precedence over text/*
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','plain',frozenset())),
			libmedia.Type(('text','*',frozenset())),
			50
		)
	)

	# validate that text/*'s greater quality gives it priority
	range = libmedia.Range.from_bytes(
		b'application/xml;q=0.4,text/*;q = 0.5,text/xml;q=0.2')

	selection = range.query(
		libmedia.Type(('application','xml',frozenset())),
		libmedia.Type(('text','plain',frozenset())),
	)
	# text/xml should have precedence over text/*
	test.fail_if_not_equal(selection, (
			libmedia.Type(('text','plain',frozenset())),
			libmedia.Type(('text','*',frozenset())),
			50
		)
	)

	# reveal precedence
	range = libmedia.Range.from_bytes(
		b'text/html,text/html ;  level=\n	1  ,text/*') # whitespace to exercise strip()

	html_l1 = libmedia.Type(('text','html',frozenset([('level','1')])))
	selection = range.query(html_l1)
	# text/html;level=1 should have precedence over text/* and text/html
	test.fail_if_not_equal(selection, (html_l1, html_l1, 100))

	# quotes
	range = libmedia.Range.from_string(
		'text/html;foo="me\\h;,\\"",text/xml')

	text_html_foo = libmedia.Type(('text','html',frozenset([('foo','meh;,"')])))
	text_html = libmedia.Type(('text','html',frozenset()))
	selection = range.query(text_html)
	# text/html;level=1 should have precedence over text/* and text/html
	test.fail_if_not_equal(selection, (text_html, text_html_foo, 100))

if __name__ == '__main__':
	from dev import libtest; libtest.execmodule()
