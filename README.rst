==========
pytest-tcp
==========

.. image:: https://github.com/softwareTestingResearch/pytest-tcp/workflows/CI/badge.svg
    :target: https://github.com/softwareTestingResearch/pytest-tcp/actions?workflow=CI
    :alt: Build status

.. image:: https://img.shields.io/pypi/pyversions/pytest-tcp.svg
    :target: https://pypi.org/project/pytest-tcp
    :alt: PyPI versions

.. image:: https://results.pre-commit.ci/badge/github/pre-commit/pre-commit/main.svg
   :target: https://results.pre-commit.ci/latest/github/pre-commit/pre-commit/main
   :alt: pre-commit.ci status

Pytest plugin for test-case prioritization

----

This `pytest`_ plugin allows you to find failures faster and receive sooner debugging feedback from CI.
It does so by prioritizing running tests that have shorter execution time and/or recently failed.


Installation
------------

You can install "pytest-tcp" via `pip`_ from `PyPI`_

.. code-block:: bash

    pip install pytest-tcp


Usage
-----

Pytest will automatically find the plugin and use it when you run ``pytest``.
You can use the default prioritization heuristic
(run tests that have shorter execution time first)
by passing the ``--tcp`` option:

.. code-block:: bash

    pytest --tcp

The terminal output will tell you the current configurations
and runtime overhead of this plugin:

.. codeblock:: bash

    Using TCP weights ...
    Collect TCP features took ...
    Compute TCP order took ...


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
``pytest.ini`` (or `other configuration
file <https://docs.pytest.org/en/latest/reference/customize.html#configuration>`__):

.. code-block:: ini

    [pytest]
    addopts = --tcp --tcp-weight=0.5-0.5


Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-tcp" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.


.. _`MIT`: http://opensource.org/licenses/MIT
.. _`file an issue`: https://github.com/softwareTestingResearch/pytest-tcp/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
