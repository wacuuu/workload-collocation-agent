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
        '-l',
        '--log-level',
        help='Log level for modules (by default for owca) in [module:]level form,'
             'where level can be one of: CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE'
             'Example -l debug -l example:debug'
             'Can be overridden at runtime with config.yaml "loggers" section.',
        default=['info'],
        action='append',
        dest='levels',
    )
    parser.add_argument(
        '-r', '--register', action='append', dest='components',
        help="Register additional components in config", default=[])
    parser.add_argument(
        '-v', '--version', action='version', version=platforms.get_owca_version(),
        help="Show version")

    args = parser.parse_args()

    # Initialize logging subsystem from command line options.
    log_levels = logger.parse_loggers_from_list(args.levels)
    logger.configure_loggers_from_dict(log_levels)

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

    # Configure loggers using configuration file.
    if 'loggers' in configuration:
        log_levels_config = configuration['loggers']
        if not isinstance(log_levels, dict):
            log.error('Loggers configuration error: log levels are mapping from logger name to'
                      'log level got "%r" instead!' % log_levels_config)
            exit(1)
        # Merge config from cmd line and config file.
        # Overide config file values with values provided from command line.
        log_levels = dict(log_levels, **log_levels_config)
        logger.configure_loggers_from_dict(log_levels)

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
