import argparse
import ast
import logging
import subprocess
import shlex
import threading
from functools import partial

from owca.storage import KafkaStorage
from owca.wrapper.parser import default_parse, parse_loop, DEFAULT_REGEXP, ParseFunc
from owca.wrapper.server import run_server
from owca.platforms import get_owca_version

log = logging.getLogger(__name__)


def main(parse: ParseFunc = default_parse):
    """
    Launches workload and parser with processed arguments. Handles workload shutdown.
    """
    arg_parser = prepare_argument_parser()
    # It is assumed that unknown arguments should be passed to workload.
    args = arg_parser.parse_args()

    # Configuring log
    logging.basicConfig(level=args.log_level)
    log.debug("Logger configured with {0}".format(args.log_level))
    log.info("Starting wrapper version {}".format(get_owca_version()))

    command_splited = shlex.split(args.command)
    log.info("Running command: {}".format(command_splited))
    workload_process = subprocess.Popen(command_splited,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        universal_newlines=True,
                                        bufsize=1024)

    input = workload_process.stderr if args.stderr else workload_process.stdout

    labels = ast.literal_eval(args.labels)
    parse = partial(parse, regexp=args.regexp, separator=args.separator, labels=labels, input=input)

    # create kafka storage with list of kafka brokers from arguments
    kafka_brokers_addresses = args.kafka_brokers.replace(" ", "").split(',')
    if kafka_brokers_addresses != [""]:
        log.info("KafkaStorage {}".format(kafka_brokers_addresses))
        kafka_storage = KafkaStorage(brokers_ips=kafka_brokers_addresses,
                                     max_timeout_in_seconds=5.0,
                                     topic=args.kafka_topic)
    else:
        kafka_storage = None

    t = threading.Thread(target=parse_loop, args=(parse, kafka_storage))
    t.start()
    if args.ip != "":
        # this blocks until it catches KeyboardInterrupt
        run_server(ip=args.ip, port=args.port)
    else:
        # Wait for parser thread to terminate.
        t.join()

    # terminate all spawned processes
    workload_process.terminate()


def prepare_argument_parser():
    parser = argparse.ArgumentParser(
        description='Wrapper that exposes APMs over HTTP using Prometheus format.'
    )
    parser.add_argument(
        '--prometheus_port',
        help='Port to be used to expose the metrics',
        dest='port',
        default=9000,
        type=int)
    parser.add_argument(
        '--prometheus_ip',
        help='IP used to expose the metrics',
        dest='ip',
        default='',
        type=str
    )
    parser.add_argument(
        '--command',
        help='Workload run command',
        dest='command',
        required=True,
        type=str
    )
    parser.add_argument(
        '--stderr',
        help='If 0, parser will use stdout, if 1 stderr',
        dest='stderr',
        default=0,
        type=int
    )
    parser.add_argument(
        '--regexp',
        help='regexp used for parsing with the default parsing function\n'
             'Needs to contain 2 named groups "name" and "value"'
             'Defaults to {0} that matches values in format "a=4.0"'.format(DEFAULT_REGEXP),
        dest='regexp',
        type=str,
        default=DEFAULT_REGEXP
    )
    parser.add_argument(
        '--separator',
        help='String that separates workload outputs',
        dest='separator',
        type=str,
        default=None
    )
    parser.add_argument(
        '--log_level',
        help='Logging level',
        dest='log_level',
        default='ERROR',
        choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'],
        type=str)
    parser.add_argument(
        '--labels',
        help="Prometheus labels. Provide them in a dict format."
             "Example: ""{'workload':'stress-ng','exper':'2'}""",
        dest='labels',
        type=str,
        default="{}"
    )
    parser.add_argument(
        '--kafka_brokers',
        help='list of addresses with ports of kafka brokers (kafka nodes). Coma separated',
        dest='kafka_brokers',
        default="",
        type=str
    )
    parser.add_argument(
        '--kafka_topic',
        help='Kafka messages topic, passed to KafkaStorage',
        dest='kafka_topic',
        default='owca_apms',
        type=str
    )
    return parser


if __name__ == "__main__":
    main()
