"""
# XML interface set for &..text schemas.

# [ Properties ]

# /(&typing.Mapping)namespaces
	# The namespace label (schema module basename) associated with the namespace URI.
"""
import typing

from ..xml import library as libxml, libschema
from ..system import libfactor

from . import schemas

namespaces = libschema.index_namespace_labels(schemas)

class Text(libschema.Interface):
	"""
	# XML text structure interfaces.
	"""
	from .schemas import txt as schema
	schema = libfactor.package_inducted(schema) / 'pf.lnk'
	namespace = namespaces['txt']
