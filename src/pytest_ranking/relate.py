from __future__ import annotations

import glob
import hashlib
import os
import re
import time

from _pytest.config import Config
from _pytest.nodes import Item

from .plugin_utils import DATA_DIR


def tokenize(string: str) -> list[str]:
    return re.findall(r'[a-zA-Z0-9]+', string.lower())


class changeRelatedness:
    def __init__(self, pytest_config: Config) -> None:
        self.pytest_config = pytest_config
        self.delta = set()

    def get_all_file_paths(self):
        """Get all file paths in the codebase"""
        pattern = os.path.join(self.pytest_config.rootpath, "**/*.py")
        file_paths = glob.glob(pattern, recursive=True)
        return file_paths

    def get_hash(self, file_path):
        """Compute hash for the file"""
        with open(file_path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()

    def get_delta(self) -> int:
        """
        Compute hashes for all files,
        get token set for files whose hashes differ or have not been seen,
        those are the changed or new files since last run (delta).
        Save the newest hashes for all files.
        *Return the number of files to compute hashes
        """
        file_paths = self.get_all_file_paths()
        hashes = {path: self.get_hash(path) for path in file_paths}

        key = os.path.join(DATA_DIR, "file_hashes")
        # load file hashes since last run
        old_hashes = self.pytest_config.cache.get(key, {})
        # save newest hashes anyway
        self.pytest_config.cache.set(key, hashes)

        # if hashes are computed for the first time
        if old_hashes == {}:
            return len(file_paths)

        # get files with a different/new hash since last run
        num_delta_files = 0
        for path, hash in hashes.items():
            if path not in old_hashes or old_hashes[path] != hash:
                self.delta = self.delta.union(tokenize(path))
                num_delta_files += 1
        return num_delta_files

    def compute_test_suite_relatedness(self, items: list[Item]) -> None:
        """Compute and save relatedness to changed files per test"""
        ret = {}
        for item in items:
            test_tokens = set(tokenize(item.nodeid))
            ret[item.nodeid] = len(self.delta.intersection(set(test_tokens)))
        key = os.path.join(DATA_DIR, "change_relatedness")
        self.pytest_config.cache.set(key, ret)

    def run(self, items: list[Item]) -> tuple[int, float]:
        start_time = time.time()
        num_delta_file = self.get_delta()
        self.compute_test_suite_relatedness(items)
        return num_delta_file, time.time() - start_time
