import collections
import os
from enum import Enum

import numpy as np

from .const import LEVEL


def get_test_group(nodeid: str, level: Enum) -> str:
    """Get test group of a PUT at different level.

    Given a put: folder/testfile.py::TestClass::testmethod[param1]
        - function: folder/testfile.py::TestClass:testmethod
        - module: folder/testfile.py
        - dir: folder

    Otherwise, treat each PUT as a unique test group.
    """
    test_without_param = nodeid.split("[")[0]
    test_file_path = test_without_param.split("::")[0]
    test_folder = os.path.dirname(test_file_path)
    if level == LEVEL.FUNCTION:
        return test_without_param
    elif level == LEVEL.MODULE:
        return test_file_path
    elif level == LEVEL.DIR:
        return test_folder
    else:
        return nodeid


def get_ranking(scores: dict, level: Enum, init_order: dict) -> dict:
    """Return ranking of tests by test nodeid.
        - scores: mapping between test nodeid to its score
    """
    # Get test groups.
    tests = []
    for nodeid, score in scores.items():
        group = get_test_group(nodeid, level)
        tests.append([nodeid, score, group])
    # Get aggregated score (mean) per group.
    group_scores = collections.defaultdict(list)
    for _, score, group in tests:
        group_scores[group].append(score)
    agg_group_scores = {
        group: np.mean(score_list)
        for group, score_list in group_scores.items()
    }
    # Sort tests by its aggregated group score.
    # Break tie by default order.
    tests.sort(
        key=lambda x: (agg_group_scores[x[2]], init_order[x[0]]),
    )
    return {
        nodeid: rank
        for rank, (nodeid, score, group) in enumerate(tests)
    }
