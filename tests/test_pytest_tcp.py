from __future__ import annotations

import pytest

test_method_one = \
    """
    import time

    def func(x):
        return x + 1

    def test_slow():
        time.sleep(1.5)
        assert func(4) == 5

    # FAIL
    def test_fast_fail():
        time.sleep(0.5)
        assert func(3) == 5

    def test_medium():
        time.sleep(1)
        assert func(4) == 5
    """


test_class_one = \
    """
    import time

    def func(x):
        return x + 1

    class TestClassSample:
        def test_fast(self):
            time.sleep(0.7)
            assert func(4) == 5

        # FAIL
        def test_slow_fail(self):
            time.sleep(1.7)
            assert func(3) == 5

        def test_medium(self):
            time.sleep(1.2)
            assert func(4) == 5
    """


@pytest.fixture
def mytester(pytester):
    pytester.makefile(
        ".ini",
        pytest="""
            [pytest]
            console_output_style = classic
            """,
    )
    yield pytester


def test_default(mytester):
    """Default currently is faster test first"""
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--tcp"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert faster tests are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
        ],
        consecutive=True
    )
    pass


def test_faster_test_first(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--tcp", "--tcp-weight=1-0"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert faster tests are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
        ],
        consecutive=True
    )
    pass


def test_recent_fail_first(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--tcp", "--tcp-weight=0-1"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert faster tests are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
         ],
        consecutive=True
    )
    pass


def test_55_weight(mytester):
    """When --tcp-weight=.5-.5"""
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--tcp", "--tcp-weight=.5-.5"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert faster tests are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED"
        ],
        consecutive=True
    )
    pass


def test_logging(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # should only log feature computation time
    logging_strings = (
        "Using TCP weights",
        "Collect TCP features took",
        "Compute TCP order took"
    )

    assert len([x for x in out.outlines if x.startswith(logging_strings)]) == 0

    # run with tcp
    args = ["-v", "--tcp"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(logging_strings)]) == 3


def test_invalid_weight(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )
    # run without tcp
    args = ["-v", "--tcp", "--tcp-weight=1-3"]
    out = mytester.runpytest(*args)
    error_msg = "pytest: error: argument --tcp-weight:" \
        + " Cannot parse input for `--tcp-weight`."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1
