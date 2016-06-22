"""
fault context package containing core Python projects.
"""
__factor_type__ = 'context'
__canonical__ = 'fault' # canonical package name

try:
	from . import context
except ImportError:
	pass
