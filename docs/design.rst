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
datatypes in the library.

In Imagecat, an image is a container for a set of named `layers`, and a layer
contains one or more `channels`.  For example, an image loaded by the
:class:`imagecat.load` operator might contain a layer named "C" with three
channels of RGB color data, and a layer "A" with a single channel of opacity
information.  More sophisticated workflows typical of 3D computer graphics
might involve images containing dozens of layers containing color, depth,
lighting, normal, object identity, velocity information, and more.

To accomodate this, every image in Imagecat is an instance of
:class:`imagecat.data.Image` containing a dict of :class:`str` layer names as
keys, and instances of :class:`imagecat.data.Layer` containing the layer data
as values.  Any string is a valid layer name, although some names are more
common by convention, such as "C" for RGB color information and "A" for alpha
channels.  Layer data is always stored using :class:`Numpy arrays<numpy.ndarray>`,
which always have three dimensions, in (row, column, channel) order. Most
layer data contains half-precision floating point values with linear brightness,
instead of the gamma-adjusted unsigned bytes with which you may be familiar.
Note that the third dimension is present even for single-channel layers like
alpha channels and masks, in which case its size will be one.  When working
with layers, be careful to keep in mind that (row, column) slicing is the
opposite of the (x, y) ordering normally used in image processing.  Finally,
each layer has a :class:`imagecat.data.Role`, which defines how the data in
the layer will be used.  For example, a layer with three channels might contain
RGB color information, or XYZ coordinates in world space, or XYZ velocity
vectors, or UVW coordinates in texture space.  The layer role is what distinguishes
among these cases, which is useful in visualization and I/O.

.. _graph:

Graph
-----

Imagecat operators are designed to be used with Graphcat,
https://graphcat.readthedocs.io, with which they are organized into
computational graphs that manage executing them at the right time and in the
right order.  Imagecat operators are compatible with all
:class:`graphcat.graph.Graph` derivatives, which include
:class:`graphcat.StaticGraph<graphcat.static.StaticGraph>`,
:class:`graphcat.DynamicGraph<graphcat.dynamic.DynamicGraph>`, and
:class:`graphcat.StreamingGraph<graphcat.streaming.StreamingGraph>`.

.. _named-inputs:

Named Inputs
------------

Named inputs are the objects that Graphcat uses to pass inputs from one
computational graph task to another; depending on the type of :ref:`graph` that
you're using, your Imagecat operators will be called with one of
:class:`graphcat.static.NamedInputs`, :class:`graphcat.dynamic.NamedInputs`,
or :class:`graphcat.streaming.NamedInputs`, which all have compatible APIs.

.. note::

    Since every Graphcat task has the same parameters, the reference
    documentation for each Imagecat operator lists the named input parameters
    in a separate "Named Inputs" section.

