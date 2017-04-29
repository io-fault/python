"""
# internet is a Python project providing some tools for working with DNS and
# HTTP. It is implemented with event driven operation in mind, but does not
# include any code for actually performing any communication; it merely structures
# data read from a wire and serializes data that is to be sent to the wire. It
# is intended to be a dependency of frameworks, applications, or servers that are
# implementing support for HTTP or DNS.

# [ Hyper Text Transfer Protocol ]
# --------------------------------

# HTTP processing is provided by &.http.Assembler and
# &.http.Disassembler. These generators manage the state of
# an HTTP 1.1 or 1.0 channel.

# [ Domain Name Service ]
# -----------------------

# DNS support does not yet exist. Like HTTP, it will only perform parsing
# and serialization.
"""
__factor_type__ = 'project'
