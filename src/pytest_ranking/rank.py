import os
from enum import Enum

import pandas as pd

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


def get_ranking(scores: dict, level: Enum) -> dict:
    """
    scores: a map between test nodeid to its score
    return ranking of tests by test nodeid
    """
    df = pd.DataFrame(
        data=[[k, v] for k, v in scores.items()],
        columns=["nodeid", "score"])
    df["group"] = df["nodeid"].apply(lambda x: get_test_group(x, level))
    agg_df = df[["group", "score"]].groupby(["group"]).mean().reset_index()
    agg_df = agg_df.rename(columns={"score": "agg_score"})
    df = pd.merge(df, agg_df, "left", ["group"])
    df = df.sort_values(by=["agg_score", "nodeid"], ascending=True)
    nodeids = df["nodeid"].values.tolist()
    return {nodeid: rank for rank, nodeid in enumerate(nodeids)}
