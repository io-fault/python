import sys
from ..bin import parse

txt = """
[Section 1]

Paragraph 1.

	- SetItem1
	- SetItem2
	- &Reference

/DictItem1/
	DictValue1
/DictItem2/
	DictValue2
/&Reference/
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

(title)`Paragraph Title`
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

def test_parse(test):
	"""
	# Smoke test.
	"""
	nodetree = parse.chapter(txt)

if __name__ == '__main__':
	import sys
	from ...test import engine
	engine.execute(sys.modules['__main__'])
