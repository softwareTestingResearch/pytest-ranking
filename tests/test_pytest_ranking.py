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


source_method_one = \
    """
    print("source_method_one")
    """


source_class_one = \
    """
    print("source_method_one")
    """


test_put_one = \
    """
    import pytest

    @pytest.mark.parametrize("param", {"a", "b", "c", "d"})
    def test_put_unordered(param):
        pass

    @pytest.mark.parametrize("param", ["d", "e", 1, 3, "a", "b", " "])
    def test_put_ordered(param):
        pass

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
    args = ["-v", "--rank"]
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
    args = ["-v", "--rank", "--rank-weight=1-0-0"]
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
    args = ["-v", "--rank", "--rank-weight=0-1-0"]
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


def test_550_weight(mytester):
    """--rank-weight=.5-.5-0, run recently failed and faster tests first"""
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--rank", "--rank-weight=5-5-0"]
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


def test_001_028_weight(mytester):
    """run failed tests more related to code change first"""
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--rank"]
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

    mytester.makepyfile(source_method_one=source_method_one)
    # run with tcp
    args = ["-v", "--rank", "--rank-weight=0-0-1"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert tests more related to the change are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
        ],
        consecutive=True
    )

    mytester.makepyfile(source_class_one=source_class_one)
    # run with tcp
    args = ["-v", "--rank", "--rank-weight=0-2-8"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert faster tests are run first
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
        ],
        consecutive=True
    )


def test_208_093_weight(mytester):
    """run faster tests more related to code change first"""
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # run with tcp
    args = ["-v", "--rank"]
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

    mytester.makepyfile(source_method_one=source_method_one)
    # run with tcp
    args = ["-v", "--rank", "--rank-weight=.2-0-.8"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    # assert tests more related to the change are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
        ],
        consecutive=True
    )

    mytester.makepyfile(source_class_one=source_class_one)
    # run with tcp
    args = ["-v", "--rank", "--rank-weight=0-9-3"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
        ],
        consecutive=True
    )


def test_logging(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # should only log feature computation time
    log_text = (
        "weights: ",
        "look-back history length",
        "number of *.py src files with new hashes",
        "test-change similarity compute time (s)",
        "test order compute time (s)",
        "feature collection time (s)",
    )

    header = "= pytest-ranking summary info ="
    assert len([x for x in out.outlines if header in x]) == 0
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 0

    # run with tcp
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    lines = out.outlines
    # check log text exists in plugin summary info
    header = "= pytest-ranking summary info ="
    idx = [i for i in range(len(lines)) if header in lines[i]]
    assert len(idx) == 1
    assert len([x for x in lines[idx[0]:] if x.startswith(log_text)]) == 6


def test_invalid_weight(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )
    args = ["-v", "--rank", "--rank-weight=1-3"]
    out = mytester.runpytest(*args)
    error_msg = "pytest: error: argument --rank-weight:" \
        + " Cannot parse input for `--rank-weight`."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1

    args = ["-v", "--rank", "--rank-weight=1-3-x"]
    out = mytester.runpytest(*args)
    error_msg = "pytest: error: argument --rank-weight:" \
        + " Cannot parse input for `--rank-weight`."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1


def test_random_order(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # should only log feature computation time
    log_text = (
        "weights: ",
        "look-back history length",
        "number of *.py src files with new hashes",
        "test-change similarity compute time (s)",
        "random test order with seed",
        "test order compute time (s)",
        "feature collection time (s)",
    )
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 0

    # run with default tcp
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 6

    # run with tcp with default seed
    args = ["-v", "--rank", "--rank-weight=0-0-0"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    log_text = (
        "random test order with seed: 0",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1

    # run with tcp with default seed
    args = ["-v", "--rank", "--rank-weight=0.0-0.0-0.0"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    log_text = (
        "random test order with seed: 0",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1

    # run with tcp with specific seed
    args = ["-v", "--rank", "--rank-weight=0-0-0", "--rank-seed=1234"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    log_text = (
        "random test order with seed: 1234",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1


def test_xdist(mytester):
    """Test the plugin under pytest-xdist (test parallel)"""
    mytester.makepyfile(
        test_put_one=test_put_one,
    )

    args = ["-v", "--rank", "-n", "auto", "--rank-weight=0-0-0"]
    out = mytester.runpytest(*args)
    assert len([x for x in out.outlines if x.startswith("ERROR")]) == 0
    pass
