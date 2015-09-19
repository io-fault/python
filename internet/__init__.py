"""
📡 About
--------

internet is a Python project providing some tools for working with DNS and
HTTP. It is implemented with event driven operation in mind, but does not
include any code for actually performing any communication; it merely structures
data read from a wire and serializes data that is to be sent to the wire. It
is intended to be a dependency of frameworks, applications, or servers that are
implementing support for HTTP or DNS.

Hyper Text Transfer Protocol
----------------------------

HTTP processing is providing by :py:func:`internet.libhttp.Assembler` and
:py:func:`internet.libhttp.Disassembler`. These generators manage the state of
an HTTP 1.1 or 1.0 channel.

Domain Name Service
-------------------

DNS support does not yet exist. The plan is to provide the tools for packing and
unpacking DNS record responses and queries.
"""
__pkg_bottom__ = True
