import collections
import os
from enum import Enum

import numpy as np

from .const import LEVEL


def get_test_group(nodeid: str, level: Enum) -> str:
    # format: folder/testfile.py::TestClass::testmethod[param1]
    test_without_param = nodeid.split("[")[0]
    prefix = test_without_param.split("::")[0]
    suffix = test_without_param.split("::")[-1]
    method = suffix.split("[")[0]
    file = os.path.basename(prefix)
    folder = os.path.dirname(prefix)
    if level == LEVEL.METHOD:
        return method
    elif level == LEVEL.FILE:
        return file
    elif level == LEVEL.FOLDER:
        return folder
    else:
        return nodeid


def get_ranking(scores: dict, level: Enum, init_order: dict) -> dict:
    """
    scores: a map between test nodeid to its score
    return ranking of tests by test nodeid
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
    # Sort tests by its aggregated group score,
    # break tie by default order.
    tests.sort(key=lambda x: (agg_group_scores[x[2]], x[0]))
    return {
        nodeid: rank
        for rank, (nodeid, score, group) in enumerate(tests)
    }
