import logging
import sys

# Multiple calls to logging.getLogger('someLogger') return a
# reference to the same logger object.  This is true not only
# within the same module, but also across modules as long as
# it is in the same Python interpreter process.

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s —%(funcName)s:%(lineno)d — %(message)s"
)


log_format = (
    "[%(asctime)s] — %(name)s — %(levelname)s —"
    "%(funcName)s:%(lineno)d—12s %(message)s"
)
# '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
logging.basicConfig(
    # Define logging level
    level=logging.INFO,
    # Define the format of log messages
    format=log_format,
    # Provide the filename to store the log messages
    filename=("debug.log"),
)


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler
