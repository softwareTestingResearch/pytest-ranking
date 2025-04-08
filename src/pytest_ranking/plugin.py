from __future__ import annotations

import argparse
import os
import random
import textwrap
import time
from enum import Enum

import numpy as np
import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from .change_tracker import changeTracker
from .const import (DATA_DIR, DEFAULT_HIST_LEN, DEFAULT_LEVEL, DEFAULT_SEED,
                    DEFAULT_WEIGHT, LEVEL)
from .rank import get_ranking

PLUGIN_HELP = """\
Run regression test prioritization for pytest test suite.
It re-orders execution of tests to expose test failure sooner.
"""


WEIGHT_HELP = """\
Set weights on different prioritization heuristics,
separated by hyphens `-`.
The sum of weights will be normalized to 1.
Higher weight means that heuristic will be favored.
Default value is 1-0-0.
"""

HIST_LEN_HELP = """\
The maximum number of previous test runs
that can be recorded for a test since the test has failed.
Default value is 50 (must be integer).
"""

SEED_HELP = """\
Seed when running tests in random order.
You can run random order via setting `--rank-weight=0-0-0`
Default value is time.time().
"""

LEVEL_HELP = """
The test group level at which the prioritization takes place.
Test items below the configured level follow pytest default order.
Score of a test group is the mean score over all tests in that group.
Default value is PUT.
"""


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("rank", "pytest-ranking")
    group._addoption(
        "--rank",
        action="store_true",
        help=textwrap.dedent(PLUGIN_HELP))

    group._addoption(
        "--rank-level",
        action="store",
        type=level_type,
        default=DEFAULT_LEVEL,
        dest="rank_level",
        help=textwrap.dedent(LEVEL_HELP))

    group._addoption(
        "--rank-weight",
        action="store",
        type=weight_type,
        default=DEFAULT_WEIGHT,
        dest="rank_weight",
        help=textwrap.dedent(WEIGHT_HELP))

    group._addoption(
        "--rank-hist-len",
        action="store",
        type=int,
        dest="rank_hist_len",
        default=DEFAULT_HIST_LEN,
        help=textwrap.dedent(HIST_LEN_HELP))

    group._addoption(
        "--rank-seed",
        action="store",
        type=int,
        dest="rank_seed",
        default=DEFAULT_SEED,
        help=textwrap.dedent(SEED_HELP))

    parser.addini("rank_weight", WEIGHT_HELP, default=DEFAULT_WEIGHT)
    parser.addini("rank_level", LEVEL_HELP, default=DEFAULT_LEVEL)
    parser.addini("rank_hist_len", HIST_LEN_HELP, default=DEFAULT_HIST_LEN)
    parser.addini("rank_seed", SEED_HELP, default=DEFAULT_SEED)


def weight_type(string: str) -> str:
    """Check weight format"""
    if string == DEFAULT_WEIGHT:
        return string
    try:
        weights = string.split("-")
        assert len(weights) == 3
        weights = [float(w) for w in weights]
        return string
    except (AssertionError, ValueError):
        raise argparse.ArgumentTypeError(
            "Cannot parse input for `--rank-weight`."
            + "Valid examples: 1-0-0, 0.4-0.2-0.2, and 2-7-1."
        )


def level_type(string: str) -> str:
    "Check level format"
    if string == DEFAULT_LEVEL:
        return string
    try:
        valid_levels = [i.value for i in LEVEL]
        assert string in valid_levels
        return string
    except AssertionError:
        raise argparse.ArgumentTypeError(
            "Invalid input for `--rank-level`."
            + " Please run `pytest -help` for instruction."
        )


def min_max_normalization(x: list[float]) -> np.ndarray:
    x = np.array(x)
    x_range = (np.max(x) - np.min(x))
    x = (x - np.min(x)) / x_range if x_range else np.zeros(len(x))
    return x


class RTPRunner:
    """Plugin class"""
    def __init__(self, config: Config) -> None:
        self.config = config
        self.test_reports = []
        # for logging runtime overhead, etc
        self.log = {}
        self.weights = self.parse_rtp_weights()
        self.level = self.parse_rtp_level()
        self.hist_len = self.parse_hist_len()
        self.seed = self.parse_seed()
        self.chgtracker = changeTracker(config)

    def parse_rtp_weights(self) -> list[float]:
        """Get weights, non-default CLI overrides ini file input"""
        weights = self.config.getoption("--rank-weight")
        if weights == DEFAULT_WEIGHT:
            ini_val = self.config.getini("rank_weight")
            weights = ini_val if ini_val else weights

        weights = weights.split("-")
        weights = [float(w) for w in weights]
        weight_sum = sum(weights)
        if weight_sum == 0:
            return [0, 0, 0]
        weights = [w_i / weight_sum for w_i in weights]
        return weights

    def parse_rtp_level(self) -> Enum:
        """Get granularity level for ordering"""
        level = self.config.getoption("--rank-level")
        if level == DEFAULT_LEVEL:
            ini_val = self.config.getini("rank_level")
            level = ini_val if ini_val else level
        return level

    def parse_hist_len(self) -> int:
        """Get history length, non-default CLI overrides ini file input"""
        # Get the hist len limit
        hist_len = self.config.getoption("--rank-hist-len")
        if hist_len == DEFAULT_HIST_LEN:
            ini_val = self.config.getini("rank_hist_len")
            hist_len = ini_val if ini_val else hist_len
        return int(hist_len)

    def parse_seed(self) -> int:
        """Get random seed, non-default CLI overrides ini file input"""
        rand_seed = self.config.getoption("--rank-seed")
        if rand_seed == DEFAULT_SEED:
            ini_val = self.config.getini("rank_seed")
            rand_seed = ini_val if ini_val else rand_seed
        return int(rand_seed)

    def load_feature_data(
            self,
            feature_name: str,
            items: list[Item],
            transform: bool) -> list[float]:
        """
        Load and normalize test-wise feature data for the current test suite
        transform should be True if smaller was better
        """
        # load original data
        key = os.path.join(DATA_DIR, feature_name)
        values = self.config.cache.get(key, {})
        # 0 if not exist yet implicitly prioritizes new selected/created tests
        values = [values.get(item.nodeid, 0) for item in items]
        # normalize
        values = min_max_normalization(values)
        # if smaller values is better, transform to larger is better
        if transform:
            values = 1 - values
        return values.tolist()

    def run_rtp(self, items: list[Item]) -> None:
        """Run test prioritization algorithm"""
        # get initial order from pytest, i.e., by discovery order of the tests
        init_order = {item.nodeid: i for i, item in enumerate(items)}
        # load code change features
        self.chgtracker.compute_test_suite_relatedness(items)
        num_delta_file = self.chgtracker.num_delta_files
        compute_time = self.chgtracker.overhead
        self.log["Number of changed Python files"] = num_delta_file
        self.log["Time to compute test-change similarity (s)"] = compute_time

        # start ordering tests
        start_time = time.time()

        # get initial score per test
        # test with LOWER score is run first
        scores = {}
        if self.weights == [0, 0, 0]:
            # fix input test list order for different workers in pytest-xdist
            items.sort(key=lambda item: item.nodeid)
            # randomly order with seed so that all workers have the same order
            random.seed(self.seed)
            scores = {item.nodeid: random.random() for item in items}
        else:
            w_time, w_fail, w_rel = self.weights
            h_time = self.load_feature_data("last_durations", items, True)
            h_fail = self.load_feature_data("num_runs_since_fail", items, True)
            h_rel = self.load_feature_data("change_relatedness", items, False)

            def score(i):
                # make all score negative for sorting ascendingly
                # ascending for breaking tie in default order (alphabetical)
                s = h_time[i] * w_time + h_fail[i] * w_fail + h_rel[i] * w_rel
                return -s

            scores = {item.nodeid: score(i) for i, item in enumerate(items)}

        ranks = get_ranking(scores, self.level, init_order)

        # Handle tests with declared order dependency (OD).
        od_items: list[Item] = []
        nod_items: list[Item] = []
        for item in items:
            # For https://github.com/pytest-dev/pytest-order
            # For https://github.com/RKrahl/pytest-dependency
            if (
                item.get_closest_marker('order')
                or item.get_closest_marker('dependency')
            ):
                od_items.append(item)
            else:
                nod_items.append(item)
        # Only reorder tests with no declared OD.
        nod_items.sort(
            key=lambda item: (
                ranks.get(item.nodeid, 0), init_order[item.nodeid]
            )
        )
        # Run OD tests first.
        items[:] = od_items + nod_items

        # log time to compute test order
        self.log["Time to reorder tests (s)"] = time.time() - start_time

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Record test result of each executed test"""
        if not report.skipped and report.when == "call":
            # no skipped: only look at the executed test
            # call: only look at called duration (ignore setup/teardown)
            self.test_reports.append(report)

    def pytest_report_header(self, config: Config) -> str:
        """Report plugin configurations before test session starts."""
        # Report nothing if the plugin is not enabled
        if not self.config.getoption("--rank"):
            return None
        weight = self.config.getoption("--rank-weight")
        level = self.config.getoption("--rank-level")
        hist_len = self.config.getoption("--rank-hist-len")
        random_seed = self.config.getoption("--rank-seed")
        report = [
            f"Using --rank-weight={weight}",
            f"Using --rank-level={level}",
            f"Using --rank-hist-len={hist_len}",
            f"Using --rank-seed={random_seed}",
        ]
        return "\n".join(report)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, items: list[Item]) -> None:
        if self.config.getoption("--rank"):
            self.run_rtp(items)

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        start_time = time.time()
        compute_test_features(self.config, self.test_reports, self.hist_len)
        # log time for collecting features
        self.log["Time to collect test features (s)"] = (
            time.time() - start_time
        )

    def pytest_terminal_summary(
            self, terminalreporter: TerminalReporter,
            exitstatus: int, config: Config) -> None:
        """report plugin config and overhead when it is enabled"""
        if self.config.getoption("--rank"):
            tr = terminalreporter
            tr._tw.sep("=", "pytest-ranking summary info")
            for k, v in self.log.items():
                tr._tw.line(f"{k}: {v}")
        pass


def compute_test_features(
        config: Config,
        test_reports: list[TestReport],
        hist_len: int) -> None:
    # Get the duration of the each test's most recent execution
    key = os.path.join(DATA_DIR, "last_durations")
    last_durations = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        duration = report.duration
        last_durations[nodeid] = round(duration, 3)
    config.cache.set(key, last_durations)

    # Get number of test runs since last failure
    key = os.path.join(DATA_DIR, "num_runs_since_fail")
    num_runs_since_fail = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        outcome = report.outcome
        if outcome == "failed":
            num_runs_since_fail[nodeid] = 0
        else:
            # Cap within history limit
            num_runs_since_fail[nodeid] = min(
                hist_len,
                num_runs_since_fail.get(nodeid, 0) + 1
            )
    config.cache.set(key, num_runs_since_fail)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Called when pytest is about to start:
        - Create a cache folder (if not exist) to store test features for RTP
        - Register this plugin
    """
    runner = RTPRunner(config)
    config.pluginmanager.register(runner)
