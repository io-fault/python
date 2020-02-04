"""
# Text data structures for working with paragraph content.
"""

# Paragraph primitive types.
from .types import *
# Parser
from . import document
from . import format

def parse(source,
		Parser=format.Parser,
		Transform=document.Transform,
		dt=document.Tree()
	):
	"""
	# Parse a fault-text document.
	"""

	dx = Transform(dt)
	fp = Parser()
	g = dx.process(fp.parse(source))
	return list(g)
