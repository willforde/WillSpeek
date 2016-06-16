# Standard Library Imports
import logging
import sys

# Parameters
CHUNK = 4096

# Create logger with name "spam_application"
logger = logging.getLogger("spam_application")
_consoleHandler1Stdout = logging.StreamHandler(sys.stdout)
logger.addHandler(_consoleHandler1Stdout)
logger.setLevel(logging.DEBUG)