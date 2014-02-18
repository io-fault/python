=======
Project
=======

This chapter discusses the project from a management perspective.

Introduction
============

rhythm exists to provide a pure-Python, nanosecond precision time package. It
features support for the proleptic gregorian calendar, and points and deltas of
configurable precision.

Structure
=========

This project consists of the following modules:

 :py:mod:`.rhythm.lib`
  The primary developer interface module that ties many of the other modules
  together. This is the module that is normally imported.

 :py:mod:`.rhythm.libfs`
  File system tools based on :py:mod:`.rhythm.lib`: :manpage:`stat`,
  :manpage:`fstat`, and :manpage:`lstat` calls returning the `ctime`, `mtime`, and
  `atime` as :py:class:`.rhythm.lib.Timestamp` instances.

 :py:mod:`.rhythm.libunit`
  The unit context module. This provides the standard context definition used by
  :py:mod:`.rhythm.lib`.

 :py:mod:`.rhythm.libformat`
  The implementation of standard formatting functions for parsing and
  formatting.

 :py:mod:`.rhythm.libzone`
  :py:mod:`.rhythm.libtzif` based time zone support.

 :py:mod:`.rhythm.earth`
  Definition of earth based measures of time.

 :py:mod:`.rhythm.metric`
  Definition of metric-unit based measures of time. Also earth-based.

 :py:mod:`.rhythm.gregorian`
  The implementation of gregorian-unit based time measures and points; dates,
  day deltas, and month deltas.

Requirements
============

A functioning Python interpreter and a C compiler capable of compiling Python
extension modules, clock and sleep access.

Conventions
===========

Capitalization
--------------

Often, capitalization will be used in the documentation in order to convey that
the word or phrase is being used with regards to its meaning in the context
of the project.

Terminology
-----------

 :dfn:`Horology`
  The study of and measurement of time. (definition)

 :dfn:`Unit`
  A unit of time. Normally, a typed quantity.

 :dfn:`Part`
  A measure of a particular unit in a Time instance.
  Often with regards to a `whole`.

 :dfn:`Whole`
  The unit that a selected part should be aligned to. Often, the `of`
  *keyword parameter* refers to a whole. In comments, it can be referred to
  as `of-whole`.

 :dfn:`Point`
  A point in time, however, it is a misleading designation as Points in Time
  are always vectors. Essentially, they can be treated as Points or as Vectors.
  It is a scalar quantity relative to a datum and with
  a magnitude of no less than one unit of the scalar quantity.

 :dfn:`PiT`
  Shorthand for: Point in Time.

 :dfn:`Subsecond`
  Often, a reference to the precision of representation type.

 :dfn:`Representation Type`
  An actual Python class representing a [unit] Type defined in a Time Context.

 :dfn:`Time Context`
  An instance of :py:class:`.rhythm.libunit.Context` managing the set of defined
  unit Types and any corresponding Representation Types.

 :dfn:`Canonical Position`
  A PiT that is in the understood time zone that does not vary. Usually
  referring to UTC.

 :dfn:`Localization`
  Referring to the process of localizing a timestamp to a particular time zone. Given a
  UTC timestamp, a localized version of the timestamp would be the timestamp adjusted by
  the offset identified by the specified :py:class:`.rhythm.libzone.Zone`.
  :py:meth:`.rhythm.libzone.Zone.localize`.

 :dfn:`Normalization`
  Referring the process of normalizing a localized timestamp to a particular time zone.
  Given a localized timestamp, a normalized version of the timestamp would be the
  timestamp adjusted to UTC and then localized. Normalization should be used when
  representing timestamps whose localized version has been manipulated.
  :py:meth:`.rhythm.libzone.Zone.normalize`.

 :dfn:`Term`
  Internal to rhythm: a core unit. Units are associated as "like" terms by
  :py:class:`.rhythm.libunit.Context` instances.
  In the default context, there are only two terms: days and months.

 :dfn:`Bridge`
  Internal to rhythm: a set of mappings that allow "unlike" terms to be
  converted. This is the infrastructure that provides a means to register
  the conversion methods for converting days to months and months to days.

 :dfn:`Type`
  A particular unit of time in a Time Context. `second`, `day`, `month` are
  all types.

Examples
--------

Examples will often reference a `libtime` module. This module is defined::

	from rhythm import lib as libtime

Defense
=======

This section details arguments for rhythm's existence.

Existence
---------

rhythm is the only alternative pure-Python, save clock access, datetime package.

Development
===========

Evolution
---------

rhythm strives to isolate functionality as much as possible. However, in early
implementations, difficulty came when using managing distinct units as separate
classes. Even with a common superclass, greater integration was necessary to
provide a cohesive programmer interface. Notably, when using time classes
interchangeably.

rhythm still strives, and does so with regards to basic functionality and logic.
But in order to provide the greater integration, unit classes are connected by a
Time Context that defines the consistency of all time types, and provides a
means for resolving unit conversion paths.

References
==========

The functionality and API choices of a number of datetime implementations were
analyzed during the development of rhythm:

	* Chronus-ST (http://chronos-st.org/)
	* SQL/Postgres' DATE, TIME, and TIMESTAMP types.
	* Python datetime
	* dateutils
	* mxDateTime
	* <There is another datetime package that largely influenced rhythm's API. Can't find it again...>

In addition to various packages for other languages such as ruby and java.

Wikipedia was, naturally, heavily referenced during the development of rhythm.
Here are many of the links:

 * http://en.wikipedia.org/wiki/Second
 * http://en.wikipedia.org/wiki/Julian_year_(astronomy)

Gotchas
=======

Points and Measures are Python Integers
---------------------------------------

This has the effect that integers with the same value will be seen as the same
key::

	>>> from rhythm import lib
	>>> d = {}
	>>> d[lib.Date(0)] = 'Hello, World!'
	>>> print d[0]
	Hello, World!

Month Arithmetic Can Overflow
-----------------------------

The implementation of month arithmetic is sensitive to the selected day::

	# working with a leap year
	pit = lib.Timestamp.of(iso='2012-01-31T18:55:33.946259')
	pit.elapse(month=1)
	rhythm.lib.Timestamp.of(iso='2012-03-02T18:55:33.946259')

The issue can be avoided by adjusted the PiT to the beginning of the month::

	pit = pit.update('day', 0, 'month')
