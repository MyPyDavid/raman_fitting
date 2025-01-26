from loguru import logger
import sys


logger.enable("raman_fitting")
# Remove the default logger to avoid duplicate logs
logger.remove()

# Add a new logger for console output
logger.add(sys.stderr, level="INFO")

# Add a new logger for file output
logger.add("debug.log", level="INFO", rotation="10 MB")
