import argparse
import logging

from owca_kafka_consumer.server import run_server, create_kafka_consumer


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve messages from kafka topic and expose them in HTTP server."
                    "Single threaded server reading one message per request.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--kafka_broker_addresses',
                        nargs='+',
                        default=["127.0.0.1:9092"],
                        help=("whitespace seperated list of kafka brokers"
                              "(ip with port for each)"))
    parser.add_argument('--kafka_poll_timeout',
                        default=0.3,
                        type=float,
                        help=("Timeout for reading a message from kafka while handling request."))
    parser.add_argument('--topic_name',
                        default="owca_metrics",
                        help="kafka topic name to consume messages from")
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
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    logging.info("owca_kafka_consumer was run with configuration:\n{}\n\n"
                 .format(args))
    kafka_consumer = create_kafka_consumer(args.kafka_broker_addresses,
                                           args.topic_name,
                                           args.group_id)
    run_server(ip=args.listen_ip, port=args.listen_port,
               kafka_consumer=kafka_consumer,
               kafka_poll_timeout=args.kafka_poll_timeout)


if __name__ == "__main__":
    main()
