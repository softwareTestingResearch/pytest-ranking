
# pytest-ranking



[![CI](https://github.com/softwareTestingResearch/pytest-ranking/workflows/CI/badge.svg)](https://github.com/softwareTestingResearch/pytest-ranking/actions?workflow=CI)
[![PyPI](https://img.shields.io/pypi/pyversions/pytest-ranking.svg)](https://pypi.org/project/pytest-ranking)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/softwareTestingResearch/pytest-ranking/main.svg)](https://results.pre-commit.ci/latest/github/softwareTestingResearch/pytest-ranking/main)


A Pytest plugin for reducing failure detection time of your Python test suite with automated test prioritization/ranking.

This [pytest](https://github.com/pytest-dev/pytest) plugin allows you to find failures faster and receive sooner debugging feedback from CI. It speed up test failure detection for your test suite by prioritizing the execution of tests that have shorter execution time and/or recently failed and/or more textually related to code change.

## Installation

To install `pytest-ranking` via [pip](https://pypi.org/project/pip/) from [PyPI](https://pypi.org/project):

```bash
pip install pytest-ranking
```


## Usage

Pytest will automatically find the plugin and use it when you run ``pytest``. You can use the default prioritization heuristic, which runs tests that have shorter execution time first by passing the ``--rank`` option:

```bash
pytest --rank
```

The terminal output will tell you the current configurations and runtime overhead of this plugin:

 ```text
[pytest-ranking] Weights: 1-1-0
[pytest-ranking] History length: 30
[pytest-ranking] Number of files with new hashes: 0
[pytest-ranking] Change relatedness computation time (s): 0.0007872581481933594
[pytest-ranking] Test order computation time(s): 0.00020933151245117188
```

You can configure the weights of different prioritization heuristics by additionally passing the optional `--rank-weight` flag with formatted values:

```bash
pytest --rank --rank-weight=0-1-0
```

Weights are separated by hyphens ``-``. The 1st weight is for running faster tests, the 2nd weight is for running recently failed tests, and the 3rd weight is for running tests more textually similar to the changed `*.py` files in the codebase since the last run.
All weights must be integers or floats, and the sum of their sum will be normalized to 1.
A higher weight means that a corresponding heuristic is favored. The default value is ``1-0-0``, meaning it entirely favors running faster tests.


You can also configure the maximum window size of previous test runs to compute the number of runs since a test had failed by additionally passing the optional `--rank-hist-len` flag as an integer input:

```bash
pytest --rank --rank-hist-len=30
```


You can make these options always apply by adding them to the ``addopts`` setting in your [pytest.ini](https://docs.pytest.org/en/latest/reference/customize.html#configuration).

For example, create `pytest.ini` in the codebase root folder as such:
```ini
[pytest]
addopts = --rank --rank-weight=0-1-0 --rank-hist-len=30
```

Alternatively, you can create `pytest.ini` in the codebase root folder as such:
```ini
[pytest]
rank-weight=0-1-0
rank-hist-len=30
```

and run `pytest --rank` on command line.


### Warning

Because `pytest-ranking` re-orders tests to speed up failure detection time, please disable other pytest plugins that enforeces other test orders, e.g., [pytest-randomly](https://github.com/pytest-dev/pytest-randomly), [pytest-random-order](https://github.com/pytest-dev/pytest-random-order), [pytest-reverse](https://github.com/adamchainz/pytest-reverse).


## Contributing

Contributions are very welcome. Tests can be run with [tox](https://tox.readthedocs.io/en/latest/).



## License

Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT)  license, `pytest-ranking` is free and open source software.

## Issues

If you encounter any problems, please [file an issue](https://github.com/softwareTestingResearch/pytest-ranking/issues) or [pull request](https://github.com/softwareTestingResearch/pytest-ranking/pulls) along with a detailed description.
