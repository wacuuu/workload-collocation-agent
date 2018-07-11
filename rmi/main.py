"""
Main entrypoint.

Responsbile for configuration and prepare components
and start main loop from Runner.
"""
import argparse
import logging
import os

from rmi import components
from rmi import config
from rmi import logger

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument(
    '-c', '--config',
    help="Configuration", default=None, required=True)
parser.add_argument(
    '-l', '--log-level',
    help="log levels:  CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE", default='INFO')
parser.add_argument(
    '-r', '--register', action='append', dest='components',
    help="Register additional components in config", default=[])


def main():
    args = parser.parse_args()

    # Initalize logging subsystem.
    logger.init_logging(args.log_level, package_name='rmi')
    log.debug('started PID=%r', os.getpid())

    # Register internal & external components.
    components.register_components(extra_components=args.components)

    # Initnialize all nessesary objects.
    configuration = config.load_config(args.config)

    # Extract main loop component.
    runner = configuration['runner']

    # Prepare and run the "main loop".
    runner.run()
