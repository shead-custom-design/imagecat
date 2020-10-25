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
datatypes in the library.  An image is a set of named `planes` which all share
the same resolution.  For example, a typical image loaded by the
:class:`imagecat.load` operator might contain a color plane "C" containing RGB
color information, and an alpha channel plane "A".  More sophisticated
workflows typical in 3D computer graphics might involve images containing
dozens of planes containing color, depth, normal, and lighting information.

Regardless, every image is simply a Python :class:`dict` containing
:class:`str`  keys for the plane names, and :class:`numpy.ndarray` for the
planes themselves.  Any string is a valid plane name, although some names are
more common by convention, including "C" for RGB color information and "A" for
alpha channels.  Plane arrays always have three dimensions, in (row, column,
channel) order, and typically store linear floating point values, instead of
the gamma-adjusted unsigned bytes with which you may be familiar.  Note that
the third dimension is present even for single-channel images like alpha
channels and masks, in which case its size will be one.  When working with
planes, be careful to keep in mind that (row, column) slicing is the opposite
of the (x, y) ordering normally used in image processing.
