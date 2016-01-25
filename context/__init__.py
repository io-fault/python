"""
Context Package Representation
"""
__type__ = 'context-representation'
__pkg_bottom__ = True

from ..development import extension
import_extension_module = extension.load
del extension
context = None
