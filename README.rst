==========
pytest-tcp
==========

.. image:: https://github.com/softwareTestingResearch/pytest-tcp/workflows/CI/badge.svg
    :target: https://github.com/softwareTestingResearch/pytest-tcp/actions?workflow=CI

.. image:: https://img.shields.io/pypi/pyversions/pytest-tcp.svg
    :target: https://pypi.org/project/pytest-tcp

.. image:: https://results.pre-commit.ci/badge/github/softwareTestingResearch/pytest-tcp/main.svg
   :target: https://results.pre-commit.ci/latest/github/softwareTestingResearch/pytest-tcp/main
   :alt: pre-commit.ci status


A Pytest plugin for test-case prioritization.

This `pytest`_ plugin allows you to find failures faster and receive sooner debugging feedback from CI.
It does so by prioritizing running tests that have shorter execution time and/or recently failed.


Installation
============

To install "pytest-tcp" via `pip`_ from `PyPI`_:

.. code-block:: bash

    pip install pytest-tcp


To install pytest-rerunfailures:


Usage
=====

Pytest will automatically find the plugin and use it when you run ``pytest``.
You can use the default prioritization heuristic,
which runs tests that have shorter execution time first
by passing the ``--tcp`` option:

.. code-block:: bash

    pytest --tcp

The terminal output will tell you the current configurations
and runtime overhead of this plugin::

    Using TCP weights 1-0
    Collect TCP features took 0.0029001235961914062s.
    Compute TCP order took 0.0002548694610595703s.

You can configure the weights of different prioritization heuristics
by additionally passing the ```--tcp-weight`` flag with formatted values:

.. code-block:: bash

    pytest --tcp --tcp-weight=0-1


Weights are separated by hyphens ``-``.
The 1st weight is for running faster tests,
the 2nd weight is for running recently failed tests.
The sum of all weights must equal to 1.
A higher weight means that a corresponding heuristic is favored.
The default value is ``1-0``, meaning it entirely favors running faster tests.


You can make these options always apply by adding them to the ``addopts`` setting in your
`pytest.ini <https://docs.pytest.org/en/latest/reference/customize.html#configuration>`_:

.. code-block:: ini

    [pytest]
    addopts = --tcp --tcp-weight=0.5-0.5


Contributing
============

Contributions are very welcome. Tests can be run with `tox`_.
.. , please ensure the coverage at least stays the same before you submit a pull request.

License
=======

Distributed under the terms of the `MIT`_ license, "pytest-tcp" is free and open source software


Issues
======

If you encounter any problems, please `file an issue`_ along with a detailed description.


.. _`MIT`: http://opensource.org/licenses/MIT
.. _`file an issue`: https://github.com/softwareTestingResearch/pytest-tcp/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
