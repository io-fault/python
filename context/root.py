"""
While I cannot claim total credit for the ideas that caused these implementations, it is
difficult to give due credit either because many of the conversations that led to these
projects were cited as projections. A complete bibliography may be more work than the work
or even impossible given the natural loss of memory.
"""
__type__ = 'context'
__pkg_bottom__ = True # Use this to detect the root package module of a project.
__canonical__ = __pkg_cname__ = 'fault' # canonical package name

try:
	from . import context
except ImportError:
	pass
