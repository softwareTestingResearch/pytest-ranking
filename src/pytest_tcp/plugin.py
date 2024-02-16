from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport

from .plugin_utils import DEFAULT_HIST_LEN, DEFAULT_WEIGHT, TCP_DATA_DIR
from .relate import changeRelatedness


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("tcp", "pytest-tcp")
    group._addoption(
        "--tcp",
        action="store_true",
        help="""Run test-case prioritization (TCP) algorithm.
                It reorders tests in test suite to expose test failure sooner.
                Default behavior: runs faster tests first,
                so that more tests are executed per unit time.
                See more customization in the `--tcp-weight` option.""",
    )

    group._addoption(
        "--tcp-weight",
        action="store",
        type=tcp_weight_type,
        default=DEFAULT_WEIGHT,
        help="""Weights to different TCP heuristics, separated by hyphens `-`.
                The 1st weight (w1) is for running faster tests,
                the 2nd weight (w2) is for running recently failed tests,
                the 3rd weight (w3) is for tests more related to changed files.
                The sum of all weights must equal to 1.
                A higher weight means that TCP heuristic is favored.
                Input format: `w1-w2-w3`. Default value: 1-0-0, meaning it
                entirely favors running faster tests.""",
    )


def tcp_weight_type(string: str) -> str:
    """Check weight format"""
    if string == DEFAULT_WEIGHT:
        return string
    try:
        weights = string.split("-")
        assert len(weights) == 3
        weights = [float(w) for w in weights]
        assert int(sum(weights)) == 1
        return string
    except (AssertionError, ValueError):
        raise argparse.ArgumentTypeError(
            "Cannot parse input for `--tcp-weight`."
            + "Valid examples: 1-0-0, 0.4-0.2-0.2, and .2-.7-.1."
        )


def z_score_normalization(array: list[float], reverse: bool) -> list[float]:
    array = np.array(array)
    array = (array - np.mean(array)) / np.std(array)
    if reverse:
        array = - array
    return array.tolist()


def min_max_normalization(x: list[float]) -> list[float]:
    x = np.array(x)
    x_range = (np.max(x) - np.min(x))
    x = (x - np.min(x)) / x_range if x_range else np.zeros(len(x))
    return x


class TCPRunner:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.test_reports = []
        # for logging runtime overhead, etc
        self.log = {}
        self.change_rel = changeRelatedness(config)

    def parse_tcp_weights(self) -> list[float]:
        weights = self.config.getoption("--tcp-weight")
        self.log['Test prioritization weights'] = weights

        weights = weights.split("-")
        weights = [float(w) for w in weights]
        return weights

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
        key = os.path.join(TCP_DATA_DIR, feature_name)
        values = self.config.cache.get(key, {})
        # 0 if not exist yet implicitly prioritizes new selected/created tests
        values = [values.get(item.nodeid, 0) for item in items]
        # normalize
        values = min_max_normalization(values)
        # if smaller values is better, transform to larger is better
        if transform:
            values = 1 - values
        return values.tolist()

    def run_tcp(self, items: list[Item]) -> None:
        """Run test prioritization algorithm"""
        # load code change features
        num_delta_file, compute_time = self.change_rel.run(items)
        self.log['Number of files with new hashes'] = num_delta_file
        self.log['Relatedness computation time (s)'] = compute_time

        # start ordering tests
        start_time = time.time()

        h_time = self.load_feature_data("last_durations", items, True)
        h_fail = self.load_feature_data("num_runs_since_fail", items, True)
        h_rel = self.load_feature_data("change_relatedness", items, False)
        w_time, w_fail, w_rel = self.parse_tcp_weights()

        def rank(i):
            return h_time[i] * w_time + h_fail[i] * w_fail + h_rel[i] * w_rel

        # assign priority score to each test by weighted sum
        # tests with higher priority score are run first: descending sort
        scores = {item.nodeid: rank(i) for i, item in enumerate(items)}
        items.sort(
            key=lambda item: (scores.get(item.nodeid, 0), item.nodeid),
            reverse=True)
        # log time to compute test order
        self.log["Test order computation time(s)"] = time.time() - start_time

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Record test result of each executed test case"""
        if not report.skipped and report.when == "call":
            # no skipped: only look at the executed test
            # called: only look at called duration (ignore setup/teardown)
            self.test_reports.append(report)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, items: list[Item]) -> None:
        if self.config.getoption("--tcp"):
            self.run_tcp(items)

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        start_time = time.time()
        compute_test_features(self.config, self.test_reports)
        # log time for collecting features
        self.log["Feature collection time (s)"] = time.time() - start_time

    def pytest_report_collectionfinish(self) -> list[str]:
        """
        Report time to collect TCP data and run TCP, when the plugin is enabled
        """
        report = []
        for k, v in self.log.items():
            report.append(f"[pytest-tcp] {k}: {v}")
        return report


def compute_test_features(
        config: Config,
        test_reports: list[TestReport]) -> None:
    # Get the duration of the each test's most recent execution
    key = os.path.join(TCP_DATA_DIR, "last_durations")
    last_durations = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        duration = report.duration
        last_durations[nodeid] = round(duration, 3)
    config.cache.set(key, last_durations)

    # Get number of test runs since last failure, default is tcp-hist-len
    key = os.path.join(TCP_DATA_DIR, "num_runs_since_fail")
    num_runs_since_fail = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        outcome = report.outcome
        if outcome == "failed":
            num_runs_since_fail[nodeid] = 0
        else:
            # Cap within history limit
            num_runs_since_fail[nodeid] = min(
                DEFAULT_HIST_LEN,
                num_runs_since_fail.get(nodeid, 1) + 1
            )
    config.cache.set(key, num_runs_since_fail)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Called when pytest is about to start:
        - Create a cache folder (if not exist) to store test features for tcp
        - Register this plugin
    """
    runner = TCPRunner(config)
    config.pluginmanager.register(runner)
