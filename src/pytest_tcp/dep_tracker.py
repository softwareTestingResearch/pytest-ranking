from __future__ import annotations

import glob
import hashlib
import os
from collections import defaultdict

from _pytest.config import Config
from plugin_utils import ALL_TESTS, TCP_DATA_DIR


class depTracker:
    def __init__(self, pytest_config: Config) -> None:
        self.pytest_config = pytest_config
        pass

    def get_all_file_paths(self):
        """Get all file paths in the codebase"""
        pattern = os.path.join(self.pytest_config.rootpath, "**/*.py")
        file_paths = glob.glob(pattern)
        return file_paths

    def get_hash(self, file_path):
        """Compute hash for the file"""
        with open(file_path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()

    def get_changed_files(self):
        """
        Compute hashes for all files,
        get set of files whose hashes differ or have not been seen,
        those are the changed or new files since last run (delta).
        Save the newest hashes for all files.
        """
        file_paths = self.get_all_file_paths()
        hashes = {path: self.get_hash(path) for path in file_paths}

        key = os.path.join(TCP_DATA_DIR, "file_hashes")
        # load file hashes since last run
        old_hashes = self.pytest_config.cache.get(key, {})
        # save newest hashes anyway
        self.pytest_config.cache.set(key, hashes)

        # if hashes are computed for the first time
        if old_hashes == {}:
            self.changed_files = file_paths
            return

        # get files with a different/new hash since last run
        delta = []
        for path, hash in hashes.items():
            if path not in old_hashes or old_hashes[path] != hash:
                delta.append(path)
        self.changed_files = delta

    def get_impacted_tests(self):
        """
        Get the tests impacted by the set of changed files (delta),
        by checking against test-dep mapping.
        Return all tests if the mapping does not exist.
        *The dependencies of all impacted tests will be collected
        during in current test run.
        """

        key = os.path.join(TCP_DATA_DIR, "dep_to_test")
        deps = self.pytest_config.cache.get(key, {})
        if deps == {}:
            self.impacted_tests = ALL_TESTS
            return

        impacted_tests = set()
        for file in self.delta:
            impacted_tests = impacted_tests.union(set(deps.get(file, [])))
        self.impacted_tests = list(impacted_tests)
        return

    def reverse_test_to_dep_mapping(self, test_to_dep):
        ret = defaultdict(list)
        for test, dep_files in test_to_dep.items():
            for dep_file in dep_files:
                ret[dep_file].append(test)
        ret = {k: list(set(v)) for k, v in ret.items()}
        return ret

    def save_dep_to_test_mapping(self, new_test_to_dep):
        """Collect and save dependency to test mapping to cache"""
        key = os.path.join(TCP_DATA_DIR, "dep_to_test")
        old_deps = self.pytest_config.cache.get(key, {})

        new_deps = self.reverse_test_to_dep_mapping(new_test_to_dep)
        if old_deps == {}:
            self.pytest_config.cache.set(key, new_deps)
            return

        for dep_file, tests in new_deps.items():
            old_tests = set(old_deps.get(dep_file, []))
            old_deps[dep_file] = list(set(tests).union(old_tests))
        self.pytest_config.cache.set(key, old_deps)
