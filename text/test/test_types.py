"""
# Validate the text document primitives &Paragraph and &Fragment.
"""
import sys
from .. import types as module

def test_Fragment(test):
	f = module.Fragment(('reference/hyperlink', 'http://fault.io'))
	test/tuple(f.typepath) == ('reference', 'hyperlink')

def test_Paragraph(test):
	pass

def test_Paragraph_sole(test):
	p = module.Paragraph([
		module.Fragment(('text', 'data')),
	])
	test/p.sole == module.Fragment(('text', 'data'))

def test_Paragraph_sentences(test):
	para = module.Paragraph([('text', 'A single sentence.'), ('text', ' Another sentence.')])
	t = list(para.sentences)
	test/t[0][0] == para[0]
	test/t[1][0] == para[1]

if __name__ == '__main__':
	import sys
	from ...test import library as libtest
	libtest.execute(sys.modules['__main__'])
