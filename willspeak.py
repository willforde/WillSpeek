#!/usr/bin/env python

# Standard library imports
from argparse import ArgumentParser
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s', stream=sys.stderr)


# Create Parser to parse the required arguments
parser = ArgumentParser(description="Text to speech client/server")
parser.add_argument("-s", "--server", action="store_true", default=False, help="Switch to Server Mode")
args = parser.parse_args()


# Mode Selector
if __name__ == '__main__':
    if args.server is True:
        from src import server
        server.run("localhost", 8888)
    else:
        from src import client
        client.run("localhost", 8888)
