"""
# Validate the text document primitives &Paragraph and &Fragment.
"""
import sys
from .. import core

def test_Fragment(test):
	f = core.Fragment(('reference/hyperlink', 'http://fault.io'))
	test/tuple(f.typepath) == ('reference', 'hyperlink')

def test_Paragraph(test):
	pass

def test_Paragraph_sentences(test):
	para = core.Paragraph([('text', 'A single sentence.'), ('text', ' Another sentence.')])
	test/test.sentences == para

if __name__ == '__main__':
	import sys
	from ...test import library as libtest
	libtest.execute(sys.modules['__main__'])
