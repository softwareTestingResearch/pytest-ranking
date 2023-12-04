# pytest

https://docs.pytest.org/en/7.4.x/getting-started.html#getstarted

## pytest marker
- https://docs.pytest.org/en/7.1.x/example/markers.html
- https://docs.pytest.org/en/7.1.x/how-to/mark.html#mark


You can “mark” a test function with custom metadata like this:
```python
# content of test_server.py

import pytest


@pytest.mark.webtest
def test_send_http():
    pass  # perform some webtest test for your app


def test_something_quick():
    pass


def test_another():
    pass


class TestClass:
    def test_method(self):
        pass
```

You can then restrict a test run to only run tests marked with webtest:
```
$ pytest -v -m webtest
=========================== test session starts ============================
platform linux -- Python 3.x.y, pytest-7.x.y, pluggy-1.x.y -- $PYTHON_PREFIX/bin/python
cachedir: .pytest_cache
rootdir: /home/sweet/project
collecting ... collected 4 items / 3 deselected / 1 selected

test_server.py::test_send_http PASSED                                [100%]

===================== 1 passed, 3 deselected in 0.12s ======================
```


## fixture and conftest.py

https://docs.pytest.org/en/7.1.x/reference/fixtures.html



## reordering related pytest functionalities

https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest.hookspec.pytest_collection_modifyitems


## tox
tox aims to automate and standardize testing in Python. It is part of a larger vision of easing the packaging, testing and release process of Python software.


https://tox.wiki/en/3.27.0/example/pytest.html


# pytest plugin reference

main: https://docs.pytest.org/en/7.4.x/reference/plugin_list.html#plugin-list


others:
- https://pypi.org/project/pytest-random-order/ Randomise the order in which pytest tests are run with some control over the randomness
- [BROKEN] https://pypi.org/project/pytest-random-num/ Randomise the order in which pytest tests are run with some control over the randomness
- https://pypi.org/project/pytest-relative-order/ a pytest plugin that sorts tests using "before" and "after" markers
- https://pypi.org/project/pytest-reorder/ Reorder tests depending on their paths and names
    - uses pytest_collection_modifyitems
- https://pypi.org/project/pytest-reverse/ Pytest plugin to reverse test order
    - uses pytest_collection_modifyitems
    - gets more stars if u have tests
- https://pypi.org/project/pytest-slow-last/ Run tests in order of execution time (faster tests first)
    - uses @pytest.fixture(autouse=True)
    - uses pytest_collection_modifyitems
- [NO GITHUB REPO] https://pypi.org/project/pytest-sourceorder/ A pytest plugin for ensuring tests within a class are run in source order
- https://pypi.org/project/pytest-keep-together/ Pytest plugin to customize test ordering by running all 'related' tests together
- https://pypi.org/project/pytest-order/ pytest-order is a fork of pytest-ordering that provides additional features like ordering relative to other tests
    - uses the marker order that defines when a specific test shall run, either by using an ordinal number, or by specifying the relationship to other tests
- [NO LONGER MAINTIAN] https://pypi.org/project/pytest-ordering/ moved to pytest-order



more :
- https://docs.pytest.org/en/7.1.x/explanation/flaky.html
    - https://pypi.org/project/pytest-randomly/ Pytest plugin to randomly order tests and control random.seed.
- https://github.com/anapaulagomes/pytest-picked select tests related to changed files


logging test results:
- https://github.com/hdw868/pytest-aggreport
    - https://github.com/hdw868/pytest-aggreport/blob/master/pytest_aggreport/plugin.py

template:
- https://github.com/Igorxp5/pytest-ekstazi

# pytest API reference

https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest-exit

