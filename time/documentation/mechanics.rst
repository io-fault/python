=========
Mechanics
=========

This chapter discusses the mechanics of `chronometry`. In part, this document's
intended audience are people who are interested in working on `chronometry`. However,
individuals troublshooting a dependent project may also find it useful in
order to illuminate whether an observed behaviour should be expected or *why*
`chronometry` behaves in the observed fashion.

Overview
========

The primary types represented in chronometry are the range, the measure, and the point. Measures are
concerned with mere deltas and Points are concerned with a position in time relative to a
datum.

Abstract
--------

The hierarchy of chronometry time types is relatively straightforward, but is arguably
peculiar. The Range is the base abstract class for Points and Measures. However, Points
and Measures are siblings where the Point class is dependent on the presence of a Measure
for Measurement operations such as :py:meth:`.abstract.Point.measure`.

Constraints
-----------

In earlier versions of chronometry, Points inherited from Measures. This relationship turned
out to be inappropriate as their constraints differ; the idea that a Point inherited from
a Measure made it difficult to establish the semantic distinctions.

Measures are Ranges. However, their beginning is always zero, which is in direct
opposition to Points whose Range begins at a relative offset with respect to the Datum.
Points have a constraint as well; the end of the range is always the beginning elapsed by one
unit of the representation type's maximum precision. The Measure's is end is always the magnitude of
the measure.

Points and Measures have opposing constraints; these constraints made the earlier
implementation semantically problematic as the constraint could not be inherited.

Storage
-------

The :py:mod:`.libunit` module's :py:class:`.libunit.Context` class
creates Point in Time types that are subclasses of the built-in Python `int`.

The value of the integer is an offset from the Y2K + One Day Point in Time.

The Y2K+1 datum was chosen for its nature. It's close to the beginning of a
gregorian cycle and the plus one part is used to align day units on the
beginning of a week. This alignment allows common field updates to be performed
with additional alignment specification.
