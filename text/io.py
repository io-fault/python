"""
# Primary access to kleptic text parsing and serialization functions.

#!syntax/python
	from fault.text import io as txt
	src = "[ Section ]\\nParagraph.\\n"
	element_tree = txt.structure_chapter_text(src)
	assert src == ''.join(txt.sequence_chapter_element(element_tree))
"""
from . import format
from . import document
from . import render
from . import types

def structure_paragraph_element(element, *, export=document.export) -> types.Paragraph:
	"""
	# Create a &types.Paragraph instance from the given raw paragraph &element.
	"""
	return export(element[1])

# Methods for constructing the element tree from raw parse nodes.
TreeOperations = document.Tree()

def structure_chapter_lines(lines, *,
		Parser=format.Parser,
		Transform=document.Transform,
		list=list,
	):
	"""
	# Parse kleptic text lines into an element tree.
	"""
	return list(Transform(TreeOperations).process(Parser().structure(lines)))

def structure_chapter_text(source, *, newline='\n'):
	"""
	# Parse kleptic text source into an element tree.
	"""
	return structure_chapter_lines(source.split(newline))

##
# Serialize a chapter element into a sequence of lines.
sequence_chapter_element = render.chapter
