__author__ = "David Wallace"
__docformat__ = "restructuredtext"
__status__ = "Development"
__future_package_name__ = "pyramdeconv"
__current_package_name__ = "raman_fitting"
__package_name__ = __current_package_name__

import importlib.util
import sys

try:
    from ._version import __version__
except ImportError:
    # -- Source mode --
    try:
        # use setuptools_scm to get the current version from src using git
        from setuptools_scm import get_version as _gv
        from os import path as _path

        __version__ = _gv(_path.join(_path.dirname(__file__), _path.pardir))
    except ModuleNotFoundError:
        __version__ = "importerr_modulenotfound_version"
    except Exception:
        __version__ = "importerr_exception_version"
except Exception:
    __version__ = "catch_exception_version"


# This code is written for Python 3.12 and higher
if sys.version_info.major < 3 and sys.version_info.minor < 12:
    raise RuntimeError(f"{__package_name__} requires Python 3.12 or higher.")

# Let users know if they're missing any dependencies
dependencies: set = {"numpy", "pandas", "scipy", "matplotlib", "lmfit", "pydantic"}
missing_dependencies = set()

for dependency in dependencies:
    if not importlib.util.find_spec(dependency):
        missing_dependencies.add(dependency)

if missing_dependencies:
    raise ImportError(f"Missing required dependencies {missing_dependencies}")

del dependencies, dependency, missing_dependencies

from loguru import logger  # noqa: E402

logger.disable("raman_fitting")

from .delegating.main_delegator import make_examples  # noqa: E402, F401
