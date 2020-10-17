.. image:: ../artwork/logo.png
  :width: 200px
  :align: right

.. _installation:

Installation
============

Using a Package Manager
-----------------------------

A package manager (conda, apt, yum, MacPorts, etc) should generally be your
first stop for installing Imagecat - it will make it easy to install Imagecat and
its dependencies, keep them up-to-date, and even (gasp!) uninstall them
cleanly.  If your package manager doesn't support Imagecat yet, drop them a line
and let them know you'd like them to add it!

If you're new to Python or unsure where to start, we strongly recommend taking
a look at :ref:`Anaconda <anaconda-installation>`, which the Imagecat developers
use during their day-to-day work.

.. toctree::
  :maxdepth: 2

  anaconda-installation.rst

Using Pip
---------

If your package manager doesn't support Imagecat, or doesn't have the latest
version, your next option should be Python setup tools like `pip`.  You can
always install the latest stable version of Imagecat and its required
dependencies using::

    $ pip install imagecat

... following that, you'll be able to use all of Imagecat's features.

.. _From Source:

From Source
-----------

Finally, if you want to work with the latest, bleeding-edge Imagecat goodness,
you can install it using the source code::

    $ git clone https://github.com/shead-custom-design/imagecat
    $ cd imagecat
    $ sudo python setup.py install

The setup script installs Imagecat's required dependencies and copies Imagecat into
your Python site-packages directory, ready to go.

