.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _release-notes:

Release Notes
=============

Imagecat 0.3.0 - December 4, 2020
---------------------------------

* Add support for categorical color maps.
* Added optional parameters to control the output range of imagecat.operator.uniform().
* Updated the implementation for compatibility with graphcat >= 0.10.0.
* Dramatically improved performance for imagecat.operator.composite().
* OpenEXR loader generates simplified output.

Imagecat 0.2.0 - November 23, 2020
----------------------------------

* Move functionality for image conversion to the imagecat.data module.
* Add scaling support to imagecat.operator.composite().
* Add control over the reconstruction kernel in imagecat.operator.composite().
* Made the mask input optional for imagecat.operator.composite().

Imagecat 0.1.0 - November 13, 2020
----------------------------------

* Initial Release.
