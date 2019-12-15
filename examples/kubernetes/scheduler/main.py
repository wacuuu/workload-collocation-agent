# Copyright (c) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import logging
import os

from wca.config import load_config, ConfigLoadError, register
from wca import logger

from scheduler.server import Server
from scheduler.algorithms.example_algorithm import ExampleAlgorithm

DEFAULT_MODULE = 'scheduler'

log = logging.getLogger(DEFAULT_MODULE + '.main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        help="Configuration", default=None, required=True)
    parser.add_argument(
        '-l',
        '--log-level',
        help='Log level for modules (by default for scheduler) in [module:]level form,'
             'where level can be one of: CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE'
             'Example -l debug -l example:debug. Defaults to k8s_scheduler_extender:INFO.'
             'Can be overridden at runtime with config.yaml "loggers" section.',
        default=[],
        action='append',
        dest='levels',
    )
    parser.add_argument(
        '-v', '--version', action='version', version='0.1',
        help="Show version")

    args = parser.parse_args()

    # Initialize logging subsystem from command line options.
    log_levels = logger.parse_loggers_from_list(args.levels)
    log_levels_copy_with_default = dict(**log_levels)
    log_levels_copy_with_default.setdefault(DEFAULT_MODULE, 'info')
    logger.configure_loggers_from_dict(log_levels_copy_with_default)

    log.warning('This software is pre-production and should not be deployed to production servers.')
    log.debug('started PID=%r', os.getpid())
    log.info('Starting K8s scheduler extender for Workload Collocation Agent!')

    # Initialize all necessary objects.
    register_algorithms()

    try:
        configuration = load_config(args.config)
    except ConfigLoadError as e:
        log.error('Error: Cannot load config file! : %s', e)
        exit(1)

    # Configure loggers using configuration file.
    if 'loggers' in configuration:
        log_levels_config = configuration['loggers']
        if not isinstance(log_levels, dict):
            log.error('Loggers configuration error: log levels are mapping from logger name to'
                      'log level!')
            exit(1)
        # Merge config from cmd line and config file.
        # Overwrite config file values with values provided from command line.
        log_levels = dict(log_levels_config, **log_levels)
        logger.configure_loggers_from_dict(log_levels)

    server = Server(configuration)
    server.run()


def register_algorithms():
    register(ExampleAlgorithm)


if __name__ == '__main__':
    main()
