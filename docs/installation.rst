.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _installation:

Installation
============

Imagecat
--------

To install the latest stable version of Imagecat and its dependencies, use `pip`::

    $ pip install imagecat

... once it completes, you'll be able to use all of Imagecat's core features.

OpenEXR
-------

To work with `OpenEXR <https://github.com/AcademySoftwareFoundation/openexr>`_
images, you'll need to have the OpenEXR library, which can't be installed via
pip.  If you use `Conda <https://docs.conda.io/en/latest/>`_ (which we strongly
recommend), you can install it as follows::

    $ conda install -c conda-forge openexr-python

Once you have OpenEXR, you can install Imagecat with the necessary dependencies::

    $ pip install imagecat[exr]

.. _documentation:

Documentation
-------------

We assume that you'll normally access this documentation online, but if you
want a local copy on your own computer, do the following:

First, you'll need the `pandoc <https://pandoc.org>`_ universal document
converter, which can't be installed with pip ... if you use `Conda <https://docs.conda.io/en/latest/>`_
(which we strongly recommend), you can install it with the following::

    $ conda install pandoc

Once you have pandoc, install Imagecat along with all of the dependencies needed to build the docs::

    $ pip install imagecat[doc]

Next, do the following to download a tarball to the current directory
containing all of the Imagecat source code, which includes the documentation::

    $ pip download imagecat --no-binary=:all: --no-deps

Now, you can extract the tarball contents and build the documentation (adjust the
following for the version you downloaded)::

    $ tar xzvf imagecat-0.6.1.tar.gz
    $ cd imagecat-0.6.1/docs
    $ make html
