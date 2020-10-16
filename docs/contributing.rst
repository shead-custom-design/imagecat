.. image:: ../artwork/imagecat.png
  :width: 200px
  :align: right

.. _contributing:

Contributing
============

Even if you're not in a position to contribute code to Imagecat, there are many
ways you can help the project out:

* Tell us about your tool that uses Imagecat.
* Contribute written documentation.
* Let us know about bugs.
* Spread the word!

Getting Started
---------------

If you haven't already, you'll want to get familiar with the Imagecat repository
at http://github.com/shead-custom-design/imagecat ... there, you'll find the Imagecat
sources, issue tracker, and wiki.

Next, you'll need to install Imagecat's :ref:`dependencies`.  Then, you'll be
ready to get Imagecat's source code and use setuptools to install it. To do
this, you'll almost certainly want to use "develop mode".  Develop mode is a a
feature provided by setuptools that links the Imagecat source code into the
install directory instead of copying it ... that way you can edit the source
code in your git sandbox, and you don't have to re-install it to test your
changes::

    $ git clone https://github.com/shead-custom-design/imagecat.git
    $ cd imagecat
    $ python setup.py develop

Versioning
----------

Imagecat version numbers follow the `Semantic Versioning <http://semver.org>`_ standard.

Coding Style
------------

The Imagecat source code follows the `PEP-8 Style Guide for Python Code <http://legacy.python.org/dev/peps/pep-0008>`_.

Running Regression Tests
------------------------

To run the Imagecat test suite, simply run `regression.py` from the
top-level source directory::

    $ cd imagecat
    $ python regression.py

The tests will run, providing feedback on successes / failures.

Test Coverage
-------------

When you run the test suite with `regression.py`, it also automatically
generates code coverage statistics.  To see the coverage results, open
`.cover/index.html` in a web browser.

Building the Documentation
--------------------------

To build the documentation, run::

    $ cd imagecat/docs
    $ make html

Once the documentation is built, you can view it by opening
`docs/_build/html/index.html` in a web browser.
