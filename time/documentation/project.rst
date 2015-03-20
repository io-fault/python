=======
Project
=======

This chapter discusses the project from a management perspective.

Introduction
============

chronometry exists to provide a pure-Python, nanosecond precision time package. It
features support for the proleptic gregorian calendar, and points and deltas of
configurable precision.

Structure
=========

chronometry exposes most functionality via the :py:mod:`.lib` module. The underlying
unit modules are rarely accessed directly and are primarily used by the
:py:mod:`.libunit` module which provides :py:mod:`.lib` with most of its
functionality.

:py:mod:`.libunit` is a module that defines unit base classes and defines the
standard time context that creates classes for common units--Measures and Points In Time.
The Time Context is the center of chronometry as it provides the
necessary mappings for converting unlike units. All unit-qualified Time objects have a
reference to this context.

Primarily, chronometry works with two classes that store units defined in a context: Measures
and Points. Measures are measurements of time, and Points are points in time.

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
  An instance of :py:class:`.libunit.Context` managing the set of defined
  unit Types and any corresponding Representation Types.

 :dfn:`Canonical Position`
  A PiT that is in the understood time zone that does not vary. Usually
  referring to UTC.

 :dfn:`Localization`
  Referring to the process of localizing a timestamp to a particular time zone. Given a
  UTC timestamp, a localized version of the timestamp would be the timestamp adjusted by
  the offset identified by the specified :py:class:`.libzone.Zone`.
  :py:meth:`.libzone.Zone.localize`.

 :dfn:`Normalization`
  Referring the process of normalizing a localized timestamp to a particular time zone.
  Given a localized timestamp, a normalized version of the timestamp would be the
  timestamp adjusted to UTC and then localized. Normalization should be used when
  representing timestamps whose localized version has been manipulated.
  :py:meth:`.libzone.Zone.normalize`.

 :dfn:`Term`
  Internal use only; a core unit. Units are associated as "like" terms by
  :py:class:`.libunit.Context` instances.
  In the default context, there are only two terms: days and months.

 :dfn:`Bridge`
  Internal use only; a set of mappings that allow "unlike" terms to be
  converted. This is the infrastructure that provides a means to register
  the conversion methods for converting days to months and months to days.

 :dfn:`Type`
  A particular unit of time in a Time Context. `second`, `day`, `month` are
  all types.

Defense
=======

This section details arguments for chronometry's existence.

Existence
---------

chronometry is the only alternative pure-Python, save clock access, datetime package.

Development
===========

Evolution
---------

chronometry strives to isolate functionality as much as possible. However, in early
implementations, difficulty came when using managing distinct units as separate
classes. Even with a common superclass, greater integration was necessary to
provide a cohesive programmer interface. Notably, when using time classes
interchangeably.

chronometry still strives, and does so with regards to basic functionality and logic.
But in order to provide the greater integration, unit classes are connected by a
Time Context that defines the consistency of all time types, and provides a
means for resolving unit conversion paths.

References
==========

The functionality and API choices of a number of datetime implementations were
analyzed during the development of chronometry:

	* Chronus-ST (http://chronos-st.org/)
	* SQL/Postgres' DATE, TIME, and TIMESTAMP types.
	* Python datetime
	* dateutils
	* mxDateTime
	* <There is another datetime package that largely influenced chronometry's API. Can't find it again...>

In addition to various packages for other languages such as ruby and java.

Wikipedia was, naturally, heavily referenced during the development of chronometry.
Here are many of the links:

 * http://en.wikipedia.org/wiki/Second
 * http://en.wikipedia.org/wiki/Julian_year_(astronomy)
