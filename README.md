
# pytest-tcp



[![CI](https://github.com/softwareTestingResearch/pytest-tcp/workflows/CI/badge.svg)](https://github.com/softwareTestingResearch/pytest-tcp/actions?workflow=CI)
[![PyPI](https://img.shields.io/pypi/pyversions/pytest-tcp.svg)](https://pypi.org/project/pytest-tcp)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/softwareTestingResearch/pytest-tcp/main.svg)](https://results.pre-commit.ci/latest/github/softwareTestingResearch/pytest-tcp/main)


A Pytest plugin for test-case prioritization.

This [pytest](https://github.com/pytest-dev/pytest) plugin allows you to find failures faster and receive sooner debugging feedback from CI. It speed up test failure detection for your test suite by prioritizing running tests that have shorter execution time and/or recently failed.

## Installation

To install `pytest-tcp` via [pip](https://pypi.org/project/pip/) from [PyPI](https://pypi.org/project):

```bash
pip install pytest-tcp
```


## Usage

Pytest will automatically find the plugin and use it when you run ``pytest``. You can use the default prioritization heuristic, which runs tests that have shorter execution time first by passing the ``--tcp`` option:

```bash
pytest --tcp
```

The terminal output will tell you the current configurations and runtime overhead of this plugin:

 ```text
Using TCP weights 1-0
Collect TCP features took 0.0029001235961914062s.
Compute TCP order took 0.0002548694610595703s.
```

You can configure the weights of different prioritization heuristics by additionally passing the `--tcp-weight` flag with formatted values:

```bash
pytest --tcp --tcp-weight=0-1
```

Weights are separated by hyphens ``-``. The 1st weight is for running faster tests, the 2nd weight is for running recently failed tests. The sum of all weights must equal to 1. A higher weight means that a corresponding heuristic is favored. The default value is ``1-0``, meaning it entirely favors running faster tests.

You can make these options always apply by adding them to the ``addopts`` setting in your [pytest.ini](https://docs.pytest.org/en/latest/reference/customize.html#configuration).

```ini
[pytest]

addopts = --tcp --tcp-weight=0.5-0.5
```


### Warning

Because `pytest-tcp` re-orders tests to speed up failure detection time, please disable other pytest plugins for test ordering, e.g., [pytest-randomly](https://github.com/pytest-dev/pytest-randomly), [pytest-random-order](https://github.com/pytest-dev/pytest-random-order)


## Contributing

Contributions are very welcome. Tests can be run with [tox](https://tox.readthedocs.io/en/latest/).



## License

Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT)  license, `pytest-tcp` is free and open source software.

## Issues

If you encounter any problems, please [file an issue](https://github.com/softwareTestingResearch/pytest-tcp/issues) along with a detailed description.
