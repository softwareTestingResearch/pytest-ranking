# -*- coding: utf-8 -*-

from __future__ import annotations

import random
import logging
import os
import time
import argparse
import numpy as np
from typing import List

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.main import Session

TCP_DATA_DIR = "tcp_data"
TCP_LOG_DIR = "tcp_log"
TEST_HISTORY_CACHE = "test_history"


# Default amount of historical test run results to store per test
DEFAULT_HIST_LEN = 10
DEFAULT_WEIGHT = "1-0"


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
        help="""Weights to different TCP heuristics, seperated by hyphens `-`.
                The 1st weight (w1) is for running faster tests,
                the 2nd weight (w2) is for running recently failed tests.
                The sum of all weights must equal to 1.
                A higher weight means that corresponding TCP heuristic is favored.
                Input format: `w2-w2`. Default value: 1-0, meaning it 
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
    except:
        raise argparse.ArgumentTypeError(
            "Cannot parse input for `--tcp-weight`. Valid examples: 1-0, 0.4-0.6, and .3-.7."
        )


def z_score_normalization(array: List[float], reverse: bool) -> List[float]:
    array = np.array(array)
    array = (array - np.mean(array)) / np.std(array)
    if reverse:
        array = - array
    return array.tolist()

def min_max_normalization(array: List[float], reverse: bool) -> List[float]:
    array = np.array(array)
    array = (array - np.min(array)) / (np.max(array) - np.min(array))
    if reverse:
        array = 1 - array
    return array.tolist()


class TCPRunner:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.test_reports = []

    def parse_tcp_weights(self) -> List[float]:
        weights = self.config.getoption("--tcp-weight")
        weights = weights.split("-")
        weights = [float(w) for w in weights]
        return weights

    def load_feature_data(self, feature_name: str, items: List[Item], reverse) -> List[float]:
        """Load and normalize test-wise feature data for the current test suite"""
        # load original data
        key = os.path.join(TCP_DATA_DIR, feature_name)
        values = self.config.cache.get(key, {})
        # 0 if not exist yet implicitly prioritizes new selected/created tests
        values = [values.get(i.nodeid, 0) for i in items]
        # normalize, if test with smaller value is prioritized, reverse the value
        values = min_max_normalization(values, reverse)
        return values
    
    def run_tcp(self, items: List[Item]) -> None:
        """Run test prioritization algorithm"""
        start_time = time.time()

        h_time = self.load_feature_data("last_durations", items, True)
        h_fail = self.load_feature_data("num_runs_since_fail", items, True)
        w_time, w_fail = self.parse_tcp_weights()

        # assign priority score to each test by weighted sum
        # tests with higher scores are run first
        scores = {item.nodeid: h_time[i] * w_time + h_fail[i] * w_fail for i, item in enumerate(items)}
        # logging.warning(h_time)
        # logging.warning(h_fail)
        # logging.warning(scores)
        # logging.warning(w_time)
        # logging.warning(w_fail)
        items.sort(key=lambda i: (scores.get(i.nodeid, 0), i.nodeid), reverse=True)
        
        self.run_tcp_time = time.time() - start_time

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Record test result of each executed test case"""
        if not report.skipped and report.when == "call":
            # no skipped: only look at the executed test
            # called: only look at execution time when the test is called (ignore setup/teardown)
            self.test_reports.append(report)

    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(self, items: List[Item]) -> None:
        if self.config.getoption("--tcp"):
            self.run_tcp(items)

    def pytest_sessionfinish(self, session: Session, exitstatus: int) -> None:
        start_time = time.time()
        compute_test_features(self.config, self.test_reports)
        # log time to compute test features for tcp
        key = os.path.join(TCP_DATA_DIR, "feature_collection_time")
        self.config.cache.set(key, time.time() - start_time)

    def pytest_report_collectionfinish(self) -> List[str]:
        """Report time to collect TCP data and run TCP, when the plugin is enabled"""
        report = []
        if self.config.getoption("--tcp"):
            # report configured weight
            weights = self.config.getoption("--tcp-weight")
            report.append(f"Using TCP weights {weights}")
            # report feature collection
            key = os.path.join(TCP_DATA_DIR, "feature_collection_time")
            feature_collection_time = self.config.cache.get(key, None)
            report.append(f"Collecting TCP features took {feature_collection_time} seconds.")
            # report tcp algorithm overhead
            if hasattr(self, "run_tcp_time"):
                report.append(f"Computing TCP order took {self.run_tcp_time} seconds.")
        return report


def compute_test_features(config: Config, test_reports: List[TestReport]) -> None:
    # TODO: unify the feature collection function
    # Get the duration of the each test's most recent execution
    key = os.path.join(TCP_DATA_DIR, "last_durations")
    last_durations = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        duration = report.duration
        last_durations[nodeid] = round(duration, 1)
    config.cache.set(key, last_durations)

    # Get number of test runs since last failure per test, default is tcp-hist-len
    key = os.path.join(TCP_DATA_DIR, "num_runs_since_fail")
    num_runs_since_fail = config.cache.get(key, {})
    for report in test_reports:
        nodeid = report.nodeid
        outcome = report.outcome
        if outcome == "failed":
            num_runs_since_fail[nodeid] = 0
        else:
            # Cap within history limit
            num_runs_since_fail[nodeid] = min(DEFAULT_HIST_LEN, num_runs_since_fail.get(nodeid, 1))
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
