import sys
from loguru import logger  # noqa: E402

# This code is written for Python 3.12 and higher
if sys.version_info.major < 3 and sys.version_info.minor < 12:
    raise RuntimeError("raman_fitting requires Python 3.12 or higher.")  # noqa

logger.disable("raman_fitting")

from .delegators.main_delegator import make_examples  # noqa: E402, F401
