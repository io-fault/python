"""
# Abstract Bases for Syntax related types.
"""
import abc

class Document(abc.ABCMeta):
	"""
	# Interface for Syntax Documents providing query routines
	# independent of the document's storage method.
	"""
