"""
# Python foundation projects.

# [Development Tools]

# The &..development package provides tools for managing construction of builds.

# [Application and Server Framework]

# The &..io package provides a framework for asynchronous applications. It is essentially an
# actor model implementation for event driven architectures.

# [Text Formatting Language]

# The development tools and &..factors provide a means for publishing releases with
# documentation. A form of structured text called `fault.text` is implemented by &..text
# and used by &..factors to process and structure documentation strings and comments.

# A custom language is used for consistent integration with &..factors and an XML
# focused solution for easier web publishing.
"""
__factor_type__ = 'context'
__canonical__ = 'fault' # canonical package name

try:
	from . import context
except ImportError:
	pass
