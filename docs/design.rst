.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _design:

Design
======


.. _images:

Images
------

Unsurprisingly, the overwhelming majority of operators in Imagecat either
generate, modify, or consume `images`, making them one of the most important
datatypes in the library.  An image is a container for a set of named `layers`,
and a layer contains a set of one-or-more named `components`.  For example, an
image loaded by the :class:`imagecat.load` operator might contain a layer "C"
containing "R", "G", and "B" color components, plus a layer "A" containing a
single unnamed component storing opacity information.  More sophisticated
workflows typical of 3D computer graphics might involve images containing
dozens of layers containing color, depth, lighting, normal, object identity,
and velocity information.

To accomodate this, every image in Imagecat is an instance of
:class:`imagecat.data.Image` containing a dict of :class:`str` layer names as
keys, and instances of :class:`imagecat.data.Layer` containing the layer data
as values.  Any string is a valid layer name, although some names are more
common by convention, such as "C" for RGB color information and "A" for alpha
channels.  Layer data is always stored using :class:`numpy.ndarray` instances,
which always have three dimensions, in (row, column, channel) order, and
typically store half-precision floating point values with linear brightness,
instead of the gamma-adjusted unsigned bytes with which you may be familiar.
Note that the third dimension is present even for single-channel layers like
alpha channels and masks, in which case its size will be one.  When working
with layers, be careful to keep in mind that (row, column) slicing is the
opposite of the (x, y) ordering normally used in image processing.

.. _graph:

Graph
-----

Imagecat operators are designed to be used with Graphcat,
https://graphcat.readthedocs.io, with which they are organized into
computational graphs that manage executing them at the right time and in the
right order.  Imagecat operators are compatible with both
:class:`graphcat.static.StaticGraph` and :class:`graphcat.dynamic.DynamicGraph`
Graphcat graphs.

.. _named-inputs:

Named Inputs
------------

Named inputs are the objects that Graphcat uses to pass inputs from one
computational graph task to another, and Imagecat operators are compatible with
both :class:`graphcat.static.NamedInputs` and :class:`graphcat.dynamic.NamedInputs`,
which have compatible APIs.

