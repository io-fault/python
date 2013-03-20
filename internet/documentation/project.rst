=======
Project
=======

Introduction
============

`internet` is a communication method agnostic internet package. By a stretch,
the package is wrought with irony due to its lack of capacity for actual
communication. It provides the very basics for working with a small set of
popular protocols defined by The Internet RFCs.

Structure
=========

`internet` primarily consists of the following modules:

 :py:mod:`internet.libmedia`
  Provides supporting functionality for the HTTP protocol such
  a MIME-Type data structure, a MIME Media Range type used
  in content negotiation.

 :py:mod:`internet.libhttp`
  Provides an assembler and disassembler for the HTTP protocol.

 :py:mod:`internet.data.http`
  Data module supporting the HTTP modules.

 :py:mod:`internet.data.dns`
  Data module supporting the DNS modules. (not implemented)

Requirements
============

Python.

Defense
=======

An *isolated*, event driven parser for DNS and HTTP does not appear to exist. Most
solutions come bundled with a framework that has significant impact on the
design of the protocol components or requires a fair amount of work in order for
the abstraction to be used successfully.

Isolation of parsing mechanisms allows the use of the components of internet
to be used in frameworks of arbitrary designs.

Bylaws
======

The `internet` project shall be guided by the following goals:

 * Provision of data structures for representing MIME types and media ranges.
 * Provision of an non-strict IRI parser and serializer.
 * Implementation of an non-strict HTTP parser for use in streaming architectures.
 * Implementation of an non-strict HTTP serializer for use in streaming architectures.
 * Provision of DNS data structures for representing Queries and Responses
   for all record types.
 * Implementation of a DNS parser for use in streaming architectures.
 * Implementation of Web Sockets built for use with the HTTP Parser implementation.
 * Maintenance of all functionality including implementation flaws and security fixes.
 * Compatible optimizations of any component provided reasonable maintenance cost.

Expansion of goals defined in the bylaws is possible in cases where significant
new Internet technology becomes present. For instance, the web sockets protocol is an
important addition.

Stability of Functionality
--------------------------

`internet` shall seek to avoid adding features and additional protocol support in
order to encourage external development and to limit releases that may be
insignificant to extant users.

Often, the best solution is a new a project.
