"""
Main entry point.

Responsible for configuration and prepare components
and start main loop from Runner.
"""
import argparse
import logging
import os

from owca import components
from owca import config
from owca import logger
from owca import platforms

log = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        help="Configuration", default=None, required=True)
    parser.add_argument(
        '-l', '--log-level',
        help="log level for owca: CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE", default='INFO')
    parser.add_argument(
        '-r', '--register', action='append', dest='components',
        help="Register additional components in config", default=[])
    parser.add_argument(
        '-v', '--version', action='version', version=platforms.get_owca_version(),
        help="Show version")

    args = parser.parse_args()

    # Initialize logging subsystem.
    logger.init_logging(args.log_level, package_name='owca')
    log.debug('started PID=%r', os.getpid())
    log.info('Version owca: %s', platforms.get_owca_version())

    # Register internal & external components.
    components.register_components(extra_components=args.components)

    # Initialize all necessary objects.
    try:
        configuration = config.load_config(args.config)
    except config.ConfigLoadError as e:
        log.error('Error: Cannot load config file %r: %s', args.config, e)
        exit(1)

    # Handle loggers section, provided by configuration file.
    if 'loggers' in configuration:
        loggers = configuration['loggers']
        if not isinstance(loggers, dict):
            log.error('Loggers configuration error: log levels are mapping from logger name to'
                      'log level got "%r" instead!' % loggers)
            exit(1)
        for logger_name, log_level in loggers.items():
            logger.init_logging(log_level, package_name=logger_name)

    # Dump loggers configurations  to debug issues with loggers.
    if os.environ.get('OWCA_DUMP_LOGGERS') == 'True':
        print('------------------------------------ Logging tree ---------------------')
        import logging_tree
        logging_tree.printout()
        print('------------------------------------ Logging tree END------------------')

    # Extract main loop component.
    runner = configuration['runner']

    # Prepare and run the "main loop".
    runner.run()


if __name__ == '__main__':
    main()
