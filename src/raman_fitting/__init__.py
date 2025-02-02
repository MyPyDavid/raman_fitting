__author__ = "David Wallace"
__docformat__ = "restructuredtext"
__status__ = "Development"
__future_package_name__ = "pyramdeconv"
__current_package_name__ = "raman_fitting"
__package_name__ = __current_package_name__

import sys
from loguru import logger  # noqa: E402

# This code is written for Python 3.12 and higher
if sys.version_info.major < 3 and sys.version_info.minor < 12:
    raise RuntimeError(f"{__package_name__} requires Python 3.12 or higher.")  # noqa

logger.disable("raman_fitting")

from .delegating.main_delegator import make_examples  # noqa: E402, F401


def version():
    from ._version import __version__

    logger.debug(
        f"{__package_name__} version {__version__}"
    )  # logging should be disabled here
    return f"{__package_name__} version {__version__}"
