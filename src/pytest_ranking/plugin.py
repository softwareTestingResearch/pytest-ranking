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
from .const import (DATA_DIR, DEFAULT_HIST_LEN, DEFAULT_LEVEL, DEFAULT_REPLAY,
                    DEFAULT_SEED, DEFAULT_WEIGHT, LEVEL)
from .rank import get_ranking

PLUGIN_HELP = textwrap.dedent("""\
Run regression test prioritization for pytest test suite.
It re-orders execution of tests to expose test failure sooner.
""")


WEIGHT_HELP = textwrap.dedent("""\
Set weights on different prioritization heuristics,
separated by hyphens `-`.
The sum of weights will be normalized to 1.
Higher weight means that heuristic will be favored.
Default value is 1-0-0.
""")

HIST_LEN_HELP = textwrap.dedent("""\
The maximum number of previous test runs
that can be recorded for a test since the test has failed.
Default value is 50 (must be integer).
""")

SEED_HELP = textwrap.dedent("""\
Seed when running tests in random order.
You can run random order via setting `--rank-weight=0-0-0`
Default value is 0.
""")

LEVEL_HELP = textwrap.dedent("""
The test group level at which the prioritization takes place.
Test items below the configured level follow pytest default order.
Score of a test group is the mean score over all tests in that group.
Default value is PUT.
""")

REPLAY_HELP = textwrap.dedent("""
Provide a text file where each line is a test ID.
pytest-ranking will run tests with the order defined in the file.
Default value is None.
""")


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("rank", "pytest-ranking")
    group._addoption(
        "--rank",
        action="store_true",
        help=PLUGIN_HELP)

    group._addoption(
        "--rank-level",
        action="store",
        type=level_type,
        default=DEFAULT_LEVEL,
        dest="rank_level",
        help=LEVEL_HELP)

    group._addoption(
        "--rank-weight",
        action="store",
        type=weight_type,
        default=DEFAULT_WEIGHT,
        dest="rank_weight",
        help=WEIGHT_HELP)

    group._addoption(
        "--rank-replay",
        action="store",
        type=replay_type,
        default=DEFAULT_REPLAY,
        dest="rank_replay",
        help=REPLAY_HELP)

    group._addoption(
        "--rank-hist-len",
        action="store",
        type=int,
        dest="rank_hist_len",
        default=DEFAULT_HIST_LEN,
        help=HIST_LEN_HELP)

    group._addoption(
        "--rank-seed",
        action="store",
        type=int,
        dest="rank_seed",
        default=DEFAULT_SEED,
        help=SEED_HELP)

    parser.addini("rank_weight", WEIGHT_HELP, default=DEFAULT_WEIGHT)
    parser.addini("rank_replay", REPLAY_HELP, default=DEFAULT_REPLAY)
    parser.addini("rank_level", LEVEL_HELP, default=DEFAULT_LEVEL)
    parser.addini("rank_hist_len", HIST_LEN_HELP, default=DEFAULT_HIST_LEN)
    parser.addini("rank_seed", SEED_HELP, default=DEFAULT_SEED)


def weight_type(string: str) -> str:
    """Check weight format."""
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
    "Check level format."
    if string == DEFAULT_LEVEL:
        return string
    try:
        valid_levels = [i.value for i in LEVEL]
        assert string in valid_levels
        return string
    except AssertionError:
        raise argparse.ArgumentTypeError(
            "Invalid input for `--rank-level`."
            + " Please run `pytest --help` for instruction."
        )


def replay_type(string: str) -> str:
    "Check replay file format."
    if string == DEFAULT_REPLAY:
        return string
    try:
        with open(string) as f:
            _ = f.readlines()
        return string
    except Exception:
        raise argparse.ArgumentTypeError(
            "File provided to `--rank-replay` cannot be read."
            + " Please run `pytest --help` for instruction."
        )


def min_max_normalization(x: list[float]) -> np.ndarray:
    x = np.array(x)
    x_range = (np.max(x) - np.min(x))
    x = (x - np.min(x)) / x_range if x_range else np.zeros(len(x))
    return x


class RTPRunner:
    """Plugin class."""
    def __init__(self, config: Config) -> None:
        self.config = config
        self.test_reports = []
        self.log = {}
        self.weights = self.parse_rtp_weights()
        self.level = self.parse_rtp_level()
        self.replay_file = self.parse_replay()
        self.hist_len = self.parse_hist_len()
        self.seed = self.parse_seed()
        self.chgtracker = changeTracker(config)

    def parse_rtp_weights(self) -> list[float]:
        """Get weights, non-default CLI overrides ini file input."""
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
        """Get test group level, non-default CLI overrides ini file input."""
        level = self.config.getoption("--rank-level")
        if level == DEFAULT_LEVEL:
            ini_val = self.config.getini("rank_level")
            level = ini_val if ini_val else level
        return level

    def parse_replay(self) -> str:
        """Get replay file, non-default CLI overrides ini file input."""
        replay_file = self.config.getoption("--rank-replay")
        if replay_file == DEFAULT_REPLAY:
            ini_val = self.config.getini("rank_replay")
            replay_file = ini_val if ini_val else replay_file
        return replay_file

    def parse_hist_len(self) -> int:
        """Get history length, non-default CLI overrides ini file input."""
        hist_len = self.config.getoption("--rank-hist-len")
        if hist_len == DEFAULT_HIST_LEN:
            ini_val = self.config.getini("rank_hist_len")
            hist_len = ini_val if ini_val else hist_len
        return int(hist_len)

    def parse_seed(self) -> int:
        """Get random seed, non-default CLI overrides ini file input."""
        rand_seed = self.config.getoption("--rank-seed")
        if rand_seed == DEFAULT_SEED:
            ini_val = self.config.getini("rank_seed")
            rand_seed = ini_val if ini_val else rand_seed
        return int(rand_seed)

    def load_feature(
            self,
            feature_name: str,
            items: list[Item],
            reverse: bool) -> list[float]:
        """
        Load and normalize test-wise feature data for the current test suite,
            - reverse: True if originally smaller value means higher priority.
        """
        # Load original data.
        key = os.path.join(DATA_DIR, feature_name)
        values = self.config.cache.get(key, {})
        # 0 if not exist: prioritizes newly selected/created tests.
        values = [values.get(item.nodeid, 0) for item in items]
        # Normalize to [0, 1] range.
        values = min_max_normalization(values)
        # If smaller values is better, transform to larger is better.
        if reverse:
            values = 1 - values
        return values.tolist()

    def run_rtp(self, items: list[Item]) -> None:
        """Run test prioritization algorithm."""
        # Get pytest default order.
        init_order = {item.nodeid: i for i, item in enumerate(items)}
        # Load code change features.
        self.chgtracker.compute_test_suite_similarity(items)
        num_delta_file = self.chgtracker.num_delta_files
        compute_time = self.chgtracker.runtime
        self.log["Number of changed Python files"] = num_delta_file
        self.log["Time to compute test-change similarity (s)"] = compute_time

        # Start reordering.
        start_time = time.time()

        # Get priority score per test, prioritized tests have LOWER scores.
        scores = {}
        if self.replay_file and os.path.exists(self.replay_file):
            # Run tests in the order specified in the replay file.
            with open(self.replay_file) as f:
                test_list = [x.strip() for x in f.readlines()]
                scores = {x: i for i, x in enumerate(test_list)}
        elif self.weights == [0, 0, 0]:
            # Run tests in random order.
            # Pre-sort so that all workers gets the same order in pytest-xdist.
            # https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html
            items.sort(key=lambda item: item.nodeid)
            random.seed(self.seed)
            scores = {item.nodeid: random.random() for item in items}
        else:
            # Prioritize by test features.
            w_time, w_fail, w_rel = self.weights
            h_time = self.load_feature("last_durations", items, True)
            h_fail = self.load_feature("num_runs_since_fail", items, True)
            h_rel = self.load_feature("change_similarity", items, False)

            def hybrid(i):
                # Linearly combine different heurisic values.
                # The higher, the earlier the test will be run.
                s = h_time[i] * w_time + h_fail[i] * w_fail + h_rel[i] * w_rel
                return -s

            scores = {item.nodeid: hybrid(i) for i, item in enumerate(items)}

        rank = get_ranking(scores, self.level, init_order)

        # Respect tests with declared order dependency (OD).
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
                rank.get(item.nodeid, 0), init_order[item.nodeid]
            )
        )
        # Run OD tests first.
        items[:] = od_items + nod_items

        # Record reordering runtime.
        self.log["Time to reorder tests (s)"] = time.time() - start_time

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Record test result of each executed test."""
        if not report.skipped and report.when == "call":
            # No skipped: only look at the executed test.
            # `call`: only look at called duration (ignore setup/teardown).
            self.test_reports.append(report)

    def pytest_report_header(self, config: Config) -> str:
        """Report plugin configurations before test session starts."""
        # Report nothing if the plugin is not enabled.
        if not self.config.getoption("--rank"):
            return None
        weight = self.config.getoption("--rank-weight")
        replay = self.config.getoption("--rank-replay")
        level = self.config.getoption("--rank-level")
        hist_len = self.config.getoption("--rank-hist-len")
        random_seed = self.config.getoption("--rank-seed")
        report = [
            f"Using --rank-weight={weight}",
            f"Using --rank-level={level}",
            f"Using --rank-hist-len={hist_len}",
            f"Using --rank-seed={random_seed}",
            f"Using --rank-replay={replay}",
        ]
        return "\n".join(report)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, items: list[Item]) -> None:
        if self.config.getoption("--rank"):
            if self.replay_file and self.weights == [0, 0, 0]:
                raise argparse.ArgumentTypeError(
                    "--rank-replay cannot be used together with random order."
                )
            self.run_rtp(items)

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        start_time = time.time()
        compute_test_features(self.config, self.test_reports, self.hist_len)
        # Record feature collection runtime.
        self.log["Time to collect test features (s)"] = (
            time.time() - start_time
        )

    def pytest_terminal_summary(
            self,
            terminalreporter: TerminalReporter,
            exitstatus: int,
            config: Config) -> None:
        """Report plugin runtime when it is enabled."""
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
    # Get the most recent execution time per test.
    key = os.path.join(DATA_DIR, "last_durations")
    last_durations = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        duration = report.duration
        last_durations[nodeid] = round(duration, 3)
    config.cache.set(key, last_durations)

    # Get the number of runs since its last failure per test.
    key = os.path.join(DATA_DIR, "num_runs_since_fail")
    num_runs_since_fail = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        outcome = report.outcome
        if outcome == "failed":
            num_runs_since_fail[nodeid] = 0
        else:
            # Cap within history limit.
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
