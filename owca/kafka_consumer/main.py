# Copyright (c) 2018 Intel Corporation
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
from pkg_resources import get_distribution, DistributionNotFound

from owca.kafka_consumer.server import run_server


def get_version():
    try:
        version = get_distribution('owca_kafka_consumer').version
    except DistributionNotFound:
        return ""
    return version


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve messages from kafka topic and expose them in HTTP server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--kafka_broker_addresses',
                        nargs='+',
                        default=["127.0.0.1:9092"],
                        help=("whitespace seperated list of kafka brokers"
                              "(ip with port for each)"))
    parser.add_argument('--topic_names',
                        nargs='+',
                        default=["owca_metrics", "owca_anomalies", "owca_apms"],
                        help="whitespace seperated list of kafka topics")
    parser.add_argument('--group_id',
                        default="owca_group",
                        help="kafka consumer group")
    parser.add_argument('--listen_ip',
                        default="127.0.0.1",
                        help="IP that HTTP server will bind to")
    parser.add_argument('--listen_port',
                        default="9099",
                        type=int,
                        help="port that HTTP server will bind to")
    parser.add_argument('-l', '--log_level',
                        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
                        help="log levels",
                        default='ERROR')
    parser.add_argument('-v', '--version', action='version',
                        version=get_version(),
                        help="Show version")
    parser.add_argument(
        '--most_recent_count',
        default=0, type=int,
        help="If set to value greater than 0, turn on 'most_recent mode': "
             "creates thread per topic and consume messages in an infinity loop,"
             "keeps N most recent messages per topic."
             "Otherwise (if set to 0) consume messsage synchronously in HTTP handler."
    )
    parser.add_argument(
        '--most_recent_influx_write_url', default=None, type=str,
        help="If set every uncommented line message, will be parsed and replicated to given url"
             "using influxdb prometheus flavored line protocol"
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    logging.info("owca_kafka_consumer version={} was executed with following arguments: {}"
                 .format(get_version(), args))

    run_server(ip=args.listen_ip, port=args.listen_port, args=args)


if __name__ == "__main__":
    main()
