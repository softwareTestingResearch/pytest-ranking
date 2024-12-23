from __future__ import annotations

import textwrap

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
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
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
    args = ["-v", "--rank", "--rank-weight=0-2-8"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
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
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
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
        "level: ",
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
    assert len([x for x in lines[idx[0]:] if x.startswith(log_text)]) == 7


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
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    # should only log feature computation time
    log_text = (
        "weights: ",
        "level: ",
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
    out.assert_outcomes(passed=4, failed=2)
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 7

    # run with tcp with default seed
    args = ["-v", "--rank", "--rank-weight=0-0-0"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "random test order with seed: 0",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1
    test_lines_with_seed_0 = [x for x in out.outlines if "::" in x]

    # run with tcp with default seed
    args = ["-v", "--rank", "--rank-weight=0.0-0.0-0.0"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "random test order with seed: 0",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1

    # run with tcp with specific seed
    args = ["-v", "--rank", "--rank-weight=0-0-0", "--rank-seed=1234"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "random test order with seed: 1234",
    )
    # should log feature computation time and tcp ordering time
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1
    test_lines_with_seed_1234 = [x for x in out.outlines if "::" in x]

    # assert test order differ by two seeds
    assert test_lines_with_seed_0 != test_lines_with_seed_1234


def test_xdist(mytester):
    """Test the plugin under pytest-xdist (test parallel)"""
    mytester.makepyfile(
        test_put_one=test_put_one,
    )

    args = ["-v", "--rank", "-n", "auto", "--rank-weight=0-0-0"]
    out = mytester.runpytest(*args)
    assert len([x for x in out.outlines if x.startswith("ERROR")]) == 0
    pass


test_a_method = \
    """
    import time

    def func(x):
        return x + 1

    def test_a_slow():
        time.sleep(1.5)
        assert func(4) == 5

    # FAIL
    def test_b_fast_fail():
        time.sleep(0.5)
        assert func(3) == 5

    def test_c_medium():
        time.sleep(1)
        assert func(4) == 5
    """


test_b_class = \
    """
    import time

    def func(x):
        return x + 1

    class TestClassA:
        def test_a_fast(self):
            time.sleep(0.7)
            assert func(4) == 5

        # FAIL
        def test_b_slow_fail(self):
            time.sleep(1.7)
            assert func(3) == 5

        def test_c_medium(self):
            time.sleep(1.2)
            assert func(4) == 5
    """

test_c_put = \
    """
    import pytest
    import time

    @pytest.mark.parametrize("param", {0.1, 0.2, 0.3, 0.4})
    def test_a_put_unordered(param):
        time.sleep(param)
        pass

    @pytest.mark.parametrize("param", [0.45, 0.25, 0.55, 0.35, 0.15])
    def test_b_put_ordered(param):
        time.sleep(param)
        pass

    """


def test_param_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=13, failed=2)

    # run with tcp
    args = ["-v", "--rank", "--rank-level=param"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=13, failed=2)
    # assert faster tests are run first at param level
    out.stdout.fnmatch_lines(
        [
            "test_c_put.py::test_a_put_unordered[0.1] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_c_put.py::test_a_put_unordered[0.2] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_a_put_unordered[0.3] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_a_put_unordered[0.4] PASSED",
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_c_medium PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED"
        ],
        consecutive=True
    )
    pass


def test_method_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=13, failed=2)

    # run with tcp
    args = ["-v", "--rank", "--rank-level=method"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=13, failed=2)
    # assert faster tests are run first at param level
    out.stdout.fnmatch_lines(
        [
            "test_c_put.py::test_a_put_unordered[0.1] PASSED",
            "test_c_put.py::test_a_put_unordered[0.2] PASSED",
            "test_c_put.py::test_a_put_unordered[0.3] PASSED",
            "test_c_put.py::test_a_put_unordered[0.4] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_c_medium PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED"
        ],
        consecutive=True
    )
    pass


def test_file_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put,
    )

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=13, failed=2)

    # run with tcp
    args = ["-v", "--rank", "--rank-level=file"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=13, failed=2)
    # assert faster tests are run first at param level
    out.stdout.fnmatch_lines(
        [
            "test_c_put.py::test_a_put_unordered[0.1] PASSED",
            "test_c_put.py::test_a_put_unordered[0.2] PASSED",
            "test_c_put.py::test_a_put_unordered[0.3] PASSED",
            "test_c_put.py::test_a_put_unordered[0.4] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED",
            "test_b_class.py::TestClassA::test_c_medium PASSED"
        ],
        consecutive=True
    )
    pass


def test_folder_level_ranking(mytester):

    a = mytester.mkdir("a")
    a.joinpath("test_a_method.py").write_text(
        textwrap.dedent(test_a_method))
    a.joinpath("test_b_class.py").write_text(
        textwrap.dedent(test_b_class))
    b = mytester.mkdir("b")
    b.joinpath("test_c_put.py").write_text(
        textwrap.dedent(test_c_put))

    # run without tcp
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=13, failed=2)

    # run with tcp
    args = ["-v", "--rank", "--rank-level=file"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no tcp
    out.assert_outcomes(passed=13, failed=2)
    # assert faster tests are run first at param level
    out.stdout.fnmatch_lines(
        [
            "b/test_c_put.py::test_a_put_unordered[0.1] PASSED",
            "b/test_c_put.py::test_a_put_unordered[0.2] PASSED",
            "b/test_c_put.py::test_a_put_unordered[0.3] PASSED",
            "b/test_c_put.py::test_a_put_unordered[0.4] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "a/test_a_method.py::test_a_slow PASSED",
            "a/test_a_method.py::test_b_fast_fail FAILED",
            "a/test_a_method.py::test_c_medium PASSED",
            "a/test_b_class.py::TestClassA::test_a_fast PASSED",
            "a/test_b_class.py::TestClassA::test_b_slow_fail FAILED",
            "a/test_b_class.py::TestClassA::test_c_medium PASSED"
        ],
        consecutive=True
    )
    pass


def test_invalid_level(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put,
    )

    args = ["-v", "--rank", "--rank-level=class"]
    out = mytester.runpytest(*args)
    error_msg = "pytest: error: argument --rank-level:" \
        + " Invalid input for `--rank-level`." \
        + " Please run `pytest -help` for instruction."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1
