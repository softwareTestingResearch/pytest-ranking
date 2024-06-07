from enum import Enum

# ------ Constants ------

DATA_DIR = "pytest_ranking_data"

# Default amount of historical test run results to store per test
DEFAULT_HIST_LEN = 50

DEFAULT_WEIGHT = "1-0-0"

DEFAULT_SEED = 0


class LEVEL(str, Enum):
    """
    the level at which test ranking takes place
    test items below that level are ranked by default order (alphabetical)
        - param: each parametrized unit test is ranked against each other
        - method: each test method is ranked against each other
        - file: each test*.py is ranked against each other,
            all test methods in a file is ranked alphabetically
        - folder: each test folder is ranked against each other
    """
    PARAM = "param"
    METHOD = "method"
    FILE = "file"
    FOLDER = "folder"


DEFAULT_LEVEL = LEVEL.PARAM
