.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _release-notes:

Release Notes
=============

Imagecat 0.7.0 - November 21, 2022
----------------------------------

* Make it easier to manage optional functionality.
* Simplify creating images from numpy arrays.
* Switch to pyproject.toml for packaging and flit for builds.
* Cleanup and organize documentation.

Imagecat 0.6.1 - October 21, 2021
---------------------------------

* Make it easier to display single-layer images in Jupyter notebooks.
* Updated the way we collect code coverage data.
* Switched from Zulip to Github Discussions for support.

Imagecat 0.6.0 - October 13, 2021
---------------------------------

* PIL reader didn't handle luma-only images correctly.
* Incorporate platform-specific regression test reference images.
* Reorganize and streamline the documentation.
* Switch from Travis-CI to GitHub Actions for continuous integration.
* Clarify where named inputs are documented.

Imagecat 0.5.0 - March 19, 2021
-------------------------------

* Cryptomatte operator works with a wider range of files, and better matches the behavior of other implementations.
* Added an option to extract clown mattes from the Cryptomatte operator, with caller control over which mattes to include.
* Missing dependencies cause failures at run time instead of import time.
* Replaced the `rgb2gray` operator with `dot`, which can created weighted combinations of layers with any depth.
* Added new layer roles for RGBA, matte, luminance, depth, UV, position, velocity, and normal data, and subsets of RGB channels.
* Substantial reorganization and cleanup of the documentation.

Imagecat 0.4.0 - December 9, 2020
---------------------------------

* Initial support for storing image metadata.
* OpenEXR loader imports metadata.
* imagecat.notebook.display() dynamically renders image layers using IPython widgets.
* Added new imagecat.data.Role enumerations for varying subsets of RGB, alpha, matte, luminance, and depth data.
* Added imagecat.operator.remap() for creating new images from arbitrary combinations of existing layers and components.
* Added support for Cryptomatte decoding.
* imagecat.data.Layer supports Jupyter rich output.
* Expanded / cleaned-up the documentation.
* Substantial reorganization of operators into separate modules.
* Removed support for explicit layer component names.

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
