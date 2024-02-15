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
from _pytest.python import Function
from _pytest.reports import TestReport
from dep_tracker import depTracker
from plugin_utils import DEFAULT_HIST_LEN, DEFAULT_WEIGHT, TCP_DATA_DIR


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
                the 2nd weight (w2) is for running recently failed tests.
                The sum of all weights must equal to 1.
                A higher weight means that TCP heuristic is favored.
                Input format: `w1-w2`. Default value: 1-0, meaning it
                entirely favors running faster tests.""",
    )


def tcp_weight_type(string: str) -> str:
    """Check weight format"""
    if string == DEFAULT_WEIGHT:
        return string
    try:
        weights = string.split("-")
        assert len(weights) == 2
        weights = [float(w) for w in weights]
        assert int(sum(weights)) == 1
        return string
    except (AssertionError, ValueError):
        raise argparse.ArgumentTypeError(
            "Cannot parse input for `--tcp-weight`."
            + "Valid examples: 1-0, 0.4-0.6, and .3-.7."
        )


def z_score_normalization(array: list[float], reverse: bool) -> list[float]:
    array = np.array(array)
    array = (array - np.mean(array)) / np.std(array)
    if reverse:
        array = - array
    return array.tolist()


def min_max_normalization(array: list[float], reverse: bool) -> list[float]:
    array = np.array(array)
    array = (array - np.min(array)) / (np.max(array) - np.min(array))
    if reverse:
        array = 1 - array
    return array.tolist()


class TCPRunner:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.test_reports = []
        self.dep_tracker = depTracker(config)
        # for tracking the runtime overhead
        self.log = {}

    def parse_tcp_weights(self) -> list[float]:
        weights = self.config.getoption("--tcp-weight")
        weights = weights.split("-")
        weights = [float(w) for w in weights]
        return weights

    def load_feature_data(
            self,
            feature_name: str,
            items: list[Item], reverse) -> list[float]:
        """
        Load and normalize test-wise feature data for the current test suite
        """
        # load original data
        key = os.path.join(TCP_DATA_DIR, feature_name)
        values = self.config.cache.get(key, {})
        # 0 if not exist yet implicitly prioritizes new selected/created tests
        values = [values.get(i.nodeid, 0) for i in items]
        # normalize, if test with smaller value is prioritized, reverse
        values = min_max_normalization(values, reverse)
        return values

    def run_tcp(self, items: list[Item]) -> None:
        """Run test prioritization algorithm"""
        start_time = time.time()

        h_time = self.load_feature_data("last_durations", items, True)
        h_fail = self.load_feature_data("num_runs_since_fail", items, True)
        w_time, w_fail = self.parse_tcp_weights()

        def priority(i):
            return h_time[i] * w_time + h_fail[i] * w_fail

        # assign priority score to each test by weighted sum
        # tests with higher scores are run first
        scores = {item.nodeid: priority(i) for i, item in enumerate(items)}
        items.sort(
            key=lambda i: (scores.get(i.nodeid, 0), i.nodeid),
            reverse=True
        )
        # log time to compute test order
        self.log["order_computation"] = time.time() - start_time

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

    def pytest_pyfunc_call(self, pyfuncitem: Function) -> None:
        # TODO: collect trace for impacted tests
        pass

    def pytest_sessionstart(self, session: Session) -> None:
        # TODO: enable only if the weight for this is not empty
        start_time = time.time()
        self.dep_tracker.get_changed_files()
        self.dep_tracker.get_impacted_tests()
        self.log["delta_computation"] = time.time() - start_time
        self.log["delta_changed_files"] = len(self.dep_tracker.changed_files)
        self.log["delta_impacted_tests"] = len(self.dep_tracker.impacted_tests)

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        start_time = time.time()
        compute_test_features(self.config, self.test_reports)
        # log time to compute test features for tcp
        self.log["feature_collection"] = time.time() - start_time

    def pytest_report_collectionfinish(self) -> list[str]:
        """
        Report time to collect TCP data and run TCP, when the plugin is enabled
        """
        report = []
        if self.config.getoption("--tcp"):
            # report configured weight
            weights = self.config.getoption("--tcp-weight")
            report.append(f"Test-Prioritization: weights {weights}")
            # report feature collection
            if 'feature_collection' in self.log:
                report.append(
                    "Test-Prioritization: feature collection "
                    + f" {self.log['feature_collection']}s.")
            if 'delta_computation' in self.log:
                # report overhead to collect changed files and impacted tests
                report.append(
                    "Test-Prioritization: delta computation "
                    + f" {self.log['delta_computation']}s, "
                    + "#changed *.py files "
                    + f"{self.log['delta_changed_files']} "
                    + "#impacted tests "
                    + f"{self.log['delta_impacted_tests']}.")
            if 'order_computation' in self.log:
                # report tcp algorithm overhead
                report.append(
                    "Test-Prioritization: order computation "
                    + f" {self.log['order_computation']}s.")
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
