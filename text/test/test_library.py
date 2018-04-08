import sys
from .. import library
from .. import core

def test_Parser_emphasis(test):
	function = core.Parser.emphasis
	test/list(function("No emphasis")) == [('text', "No emphasis")]

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1)]
	test/list(function("Some *emphasis!*")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1), ('text', ' and following.')]
	test/list(function("Some *emphasis!* and following.")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 2), ('text', ' and following.')]
	test/list(function("Some **emphasis!** and following.")) == expect

	expect = [('text', "Some "), ('emphasis', 'emphasis!', 3), ('text', ' and following.')]
	test/list(function("Some ***emphasis!*** and following.")) == expect

	# Pair of emphasized ranges.
	expect = [('text', "Some "), ('emphasis', 'emphasis!', 1),
		('text', ', '), ('emphasis', 'twice', 1), ('text', '!')]
	test/list(function("Some *emphasis!*, *twice*!")) == expect

	# Three emphasized ranges.
	expect = [('text', "Some "),
		('emphasis', 'emphasis!', 1), ('text', ', not '),
		('emphasis', 'twice', 2), ('text', ', but '),
		('emphasis', 'thrice', 1), ('text', '!')]
	test/list(function("Some *emphasis!*, not **twice**, but *thrice*!")) == expect

txt = """
[Section 1]

Paragraph 1.

	- SetItem1
	- SetItem2
	- &Reference

/DictItem1
	DictValue1
/DictItem2
	DictValue2
/&Reference
	DictValue3

Implicit Title:
	# SequenceItem1
	# SequenceItem2
	# SequenceItem3
	# &Reference

#!/pl/python
	# Typed Character Matrix

#!/pl/python
	# Subsequent Typed Character Matrix

Paragraph 3. `Inline Literal`. (With-Cast)`Inline Literal`.

Emphasis Types:
	# *Plain*
	# **Strong**
	# ***Excessive***

# References:
	# &<URL>
	# &[Section 2]
	# &NoTerminator

! WARNING:
	Admonition

! ERROR:
	Admonition
	#!/pl/python
		# AdmonitionCharacterMatrix

[Section 1 >> Subsection 1]

Subsection 1.1 Paragraph 1.

Paragraph 2. &[Section 1]

[Section 2]

Paragraph 1.

Paragraph 2.
"""

def test_document(test):
	"""
	# Construct an XML document from a fault.text document and validate its structure.

	# ! WARNING:
		# Does not perform any checks against the XML.
	"""
	xmli = library.XML.transform('txt:', txt, encoding='utf-8')
	xml = b''.join(xmli)

if __name__ == '__main__':
	import sys
	from ...test import library as libtest
	libtest.execute(sys.modules['__main__'])
