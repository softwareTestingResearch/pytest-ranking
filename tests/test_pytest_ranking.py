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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=1-0-0"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=0-1-0"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=5-5-0"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
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
    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=0-0-1"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    # assert tests more related to the change are run first
    out.stdout.fnmatch_lines(
        [
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_method_one.py::test_medium PASSED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
        ],
        consecutive=True
    )

    mytester.makepyfile(source_class_one=source_class_one)
    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=0-2-8"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
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
    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=.2-0-.8"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
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
    # Run with RTP.
    args = ["-v", "--rank", "--rank-weight=0-9-3"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
            "test_method_one.py::test_medium PASSED",
        ],
        consecutive=True
    )


def test_logging(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one
    )

    # Without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # Should print nothing.
    log_text = (
        "Using --rank-weight",
        "Using --rank-level",
        "Using --rank-hist-len",
        "Using --rank-seed",
        "Number of changed Python files",
        "Time to compute test-change similarity (s)",
        "Time to reorder tests (s)",
        "Time to collect test features (s)",
    )

    header = "= pytest-ranking summary info ="
    assert len([x for x in out.outlines if header in x]) == 0
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 0

    # Run with RTP.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=2, failed=1)
    # Should log everything.
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 8


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

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    # Should print nothing.
    log_text = (
        "Using --rank-weight",
        "Using --rank-level",
        "Using --rank-hist-len",
        "Using --rank-seed",
        "Number of changed Python files",
        "Time to compute test-change similarity (s)",
        "Time to reorder tests (s)",
        "Time to collect test features (s)",
    )
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 0

    # Run default.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    # Should log everything.
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 8

    # Run with default seed.
    args = ["-v", "--rank", "--rank-weight=0-0-0"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "Using --rank-seed=",
    )
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1
    test_lines_default1 = [x for x in out.outlines if "::" in x]

    # Run with specific seed.
    args = ["-v", "--rank", "--rank-weight=0.0-0.0-0.0", "--rank-seed=8"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "Using --rank-seed=8",
    )
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1
    test_lines_1 = [x for x in out.outlines if "::" in x]

    # Run with specific seed.
    args = ["-v", "--rank", "--rank-weight=0-0-0", "--rank-seed=16"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)
    log_text = (
        "Using --rank-seed=16",
    )
    assert len([x for x in out.outlines if x.startswith(log_text)]) == 1
    test_lines_2 = [x for x in out.outlines if "::" in x]

    # Assert test order differ by three different seeds.
    assert test_lines_default1 != test_lines_1 != test_lines_2


def test_xdist(mytester):
    """Test the plugin under pytest-xdist (test parallel)."""
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


test_c_put_ordered = \
    """
    import pytest
    import time

    @pytest.mark.parametrize("param", [0.45, 0.25, 0.55, 0.35, 0.15])
    def test_b_put_ordered(param):
        time.sleep(param)
        pass

    """


def test_put_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put,
    )

    # Without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=13, failed=2)

    # With RTP.
    args = ["-v", "--rank", "--rank-level=put"]
    out = mytester.runpytest(*args)

    # Assert outcome to be the same as if no RTP.
    out.assert_outcomes(passed=13, failed=2)
    # Assert faster tests are run first at PUT level.
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


def test_function_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put_ordered,
    )

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=9, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-level=function"]
    out = mytester.runpytest(*args)

    # Assert outcome to be the same as if no RTP.
    out.assert_outcomes(passed=9, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_c_medium PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED",
        ],
        consecutive=True
    )
    pass


def test_module_level_ranking(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_b_class=test_b_class,
        test_c_put=test_c_put_ordered,
    )

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=9, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-level=module"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=9, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED",
            "test_b_class.py::TestClassA::test_c_medium PASSED",
        ],
        consecutive=True
    )
    pass


def test_dir_level_ranking(mytester):

    a = mytester.mkdir("a")
    a.joinpath("test_a_method.py").write_text(
        textwrap.dedent(test_a_method))
    a.joinpath("test_b_class.py").write_text(
        textwrap.dedent(test_b_class))
    b = mytester.mkdir("b")
    b.joinpath("test_c_put.py").write_text(
        textwrap.dedent(test_c_put_ordered))

    # Without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=9, failed=2)

    # With RTP.
    args = ["-v", "--rank", "--rank-level=dir"]
    out = mytester.runpytest(*args)

    # Assert outcome.
    out.assert_outcomes(passed=9, failed=2)
    out.stdout.fnmatch_lines(
        [
            "b/test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "b/test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "a/test_a_method.py::test_a_slow PASSED",
            "a/test_a_method.py::test_b_fast_fail FAILED",
            "a/test_a_method.py::test_c_medium PASSED",
            "a/test_b_class.py::TestClassA::test_a_fast PASSED",
            "a/test_b_class.py::TestClassA::test_b_slow_fail FAILED",
            "a/test_b_class.py::TestClassA::test_c_medium PASSED",
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
        + " Please run `pytest --help` for instruction."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1


test_a_method_two = \
    """
    import time

    def func(x):
        return x + 1

    def test_a_slow():
        time.sleep(0.05)
        assert func(4) == 5

    # FAIL
    def test_b_fast_fail():
        time.sleep(0.01)
        assert func(3) == 5

    def test_c_medium():
        time.sleep(0.02)
        assert func(4) == 5
    """


def test_function_level_ranking_with_duplicate_methods(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_a_method_two=test_a_method_two,
        test_b_class=test_b_class,
        test_c_put=test_c_put_ordered,
    )

    # Without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=11, failed=3)

    # With RTP.
    args = ["-v", "--rank", "--rank-level=function"]
    out = mytester.runpytest(*args)

    # Assert outcome to be the same with/without RTP.
    out.assert_outcomes(passed=11, failed=3)
    # Assert that tests with the same method name,
    # i.e., from test_a_method and test_a_method_two,
    # are in two different group.
    out.stdout.fnmatch_lines(
        [
            "test_a_method_two.py::test_b_fast_fail FAILED",
            "test_a_method_two.py::test_c_medium PASSED",
            "test_a_method_two.py::test_a_slow PASSED",
            "test_c_put.py::test_b_put_ordered[0.45] PASSED",
            "test_c_put.py::test_b_put_ordered[0.25] PASSED",
            "test_c_put.py::test_b_put_ordered[0.55] PASSED",
            "test_c_put.py::test_b_put_ordered[0.35] PASSED",
            "test_c_put.py::test_b_put_ordered[0.15] PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_b_class.py::TestClassA::test_a_fast PASSED",
            "test_a_method.py::test_c_medium PASSED",
            "test_b_class.py::TestClassA::test_c_medium PASSED",
            "test_a_method.py::test_a_slow PASSED",
            "test_b_class.py::TestClassA::test_b_slow_fail FAILED",
        ],
        consecutive=True
    )
    pass


test_order = \
    """
    import pytest
    import time
    @pytest.mark.order(2)
    def test_foo():
        time.sleep(4.5)
        assert True

    @pytest.mark.order(1)
    def test_bar():
        time.sleep(5)
        assert True
    """

test_dependency = \
    """
    import pytest
    import time

    @pytest.mark.dependency()
    @pytest.mark.xfail(reason="deliberate fail")
    def test_a():
        time.sleep(4)
        assert False

    @pytest.mark.dependency()
    def test_b():
        time.sleep(3.5)
        pass

    @pytest.mark.dependency(depends=["test_a"])
    def test_c():
        time.sleep(3)
        pass

    @pytest.mark.dependency(depends=["test_b"])
    def test_d():
        time.sleep(2.5)
        pass

    @pytest.mark.dependency(depends=["test_b", "test_c"])
    def test_e():
        time.sleep(2)
        pass
    """


def test_order_dependency_marker(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
        test_order=test_order,
        test_dependency=test_dependency,
    )

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=8, failed=1, xfailed=1)

    # Run with RTP.
    args = ["-v", "--rank"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=8, failed=1, xfailed=1)
    # assert that tests with the same method name,
    # i.e., from test_a_method and test_a_method_two
    # are in two different group
    out.stdout.fnmatch_lines(
        [
            "test_dependency.py::test_a XFAIL (deliberate fail)",
            "test_dependency.py::test_b PASSED",
            "test_dependency.py::test_c PASSED",
            "test_dependency.py::test_d PASSED",
            "test_dependency.py::test_e PASSED",
            "test_order.py::test_foo PASSED",
            "test_order.py::test_bar PASSED",
            "test_a_method.py::test_b_fast_fail FAILED",
            "test_a_method.py::test_c_medium PASSED",
            "test_a_method.py::test_a_slow PASSED",
        ],
        consecutive=True
    )
    pass


replay_order_one = \
    """
    test_class_one.py::TestClassSample::test_fast
    test_class_one.py::TestClassSample::test_slow_fail
    test_method_one.py::test_medium
    test_method_one.py::test_fast_fail
    test_class_one.py::TestClassSample::test_medium
    test_method_one.py::test_slow
    """


def test_replay(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    mytester.maketxtfile(
        replay_order=replay_order_one
    )

    # Run without RTP.
    args = ["-v"]
    out = mytester.runpytest(*args)
    out.assert_outcomes(passed=4, failed=2)

    # Run with RTP.
    args = ["-v", "--rank", "--rank-replay=replay_order.txt"]
    out = mytester.runpytest(*args)

    # assert outcome to be the same as if no rtp
    out.assert_outcomes(passed=4, failed=2)
    out.stdout.fnmatch_lines(
        [
            "test_class_one.py::TestClassSample::test_fast PASSED",
            "test_class_one.py::TestClassSample::test_slow_fail FAILED",
            "test_method_one.py::test_medium PASSED",
            "test_method_one.py::test_fast_fail FAILED",
            "test_class_one.py::TestClassSample::test_medium PASSED",
            "test_method_one.py::test_slow PASSED",
        ],
        consecutive=True
    )


def test_replay_with_random(mytester):
    mytester.makepyfile(
        test_method_one=test_method_one,
        test_class_one=test_class_one,
    )

    mytester.maketxtfile(
        replay_order=replay_order_one
    )

    # Run with RTP.
    args = [
        "-v",
        "--rank",
        "--rank-replay=replay_order.txt",
        "--rank-weight=0-0-0"
    ]
    out = mytester.runpytest(*args)
    error_msg = "--rank-replay cannot be used together with random order."
    assert len([x for x in out.outlines if error_msg in x]) == 1


def test_invalid_replay(mytester):
    mytester.makepyfile(
        test_a_method=test_a_method,
    )

    args = ["-v", "--rank", "--rank-replay=order.txt"]
    out = mytester.runpytest(*args)
    error_msg = "pytest: error: argument --rank-replay:" \
        + " File provided to `--rank-replay` cannot be read." \
        + " Please run `pytest --help` for instruction."
    assert len([x for x in out.errlines if x.startswith(error_msg)]) == 1
