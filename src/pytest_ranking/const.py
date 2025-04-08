import time
from enum import Enum

# ------ Constants ------

DATA_DIR = "pytest_ranking_data"

# Default amount of historical test run results to store per test.
DEFAULT_HIST_LEN = 50

DEFAULT_WEIGHT = "1-0-0"

# Default seed for running random order.
DEFAULT_SEED = int(time.time())


class LEVEL(str, Enum):
    """The test group level at which the test suites are reordered.
    Tests within each group follows the pytest default order.
    https://docs.pytest.org/en/stable/reference/fixtures.html#fixtures
    """
    PUT = "put"
    FUNCTION = "function"
    MODULE = "module"
    DIR = "dir"


DEFAULT_LEVEL = LEVEL.PUT
