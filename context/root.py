"""
"""
__type__ = 'context'
__pkg_bottom__ = True # Use this to detect the root package module of a project.
__canonical__ = __pkg_cname__ = 'fault' # canonical package name

try:
	from . import context
except ImportError:
	pass
