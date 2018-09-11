"""
Reads one message from the queue while handling request;
single threaded (otherwise we could get out of order error in prometheus)
"""

from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import logging
from typing import List

import confluent_kafka


class KafkaConsumptionException(Exception):
    """Error while reading data from kafka topic."""
    pass


kafka_consumers = {}


def create_kafka_consumer(broker_addresses: List[str],
                          topic_name: str,
                          group_id: str) -> confluent_kafka.Consumer:
    consumer = confluent_kafka.Consumer({
        'bootstrap.servers': ",".join(broker_addresses),
        'group.id': group_id,
    })
    consumer.subscribe([topic_name])
    return consumer


def consume_one_message(kafka_consumer: confluent_kafka.Consumer) -> str:
    """read one message from kafka consumer

    :param kafka_consumer:

    Raises:
        KafkaConsumptionException if there was any error
            reading data from kafka (note: the case where
            there is no new message to read from kafka
            is not exceptional condition - no exception is
            raised then)
    """

    # With timeout=0 just immediatily checks internal driver buffer and returns if there is no
    # messages - desired behavior for just checking existance of message.
    msg = kafka_consumer.poll(timeout=0)

    # https://docs.confluent.io/current/clients/
    #    confluent-kafka-python/index.html#confluent_kafka.Consumer.poll
    #
    # * msg == None if we got timeout on poll
    # * msg.error().code() == KafkaError._PARTITION_EOF when there is
    #   no new messages (kafka responded within timeout period)
    if msg is None or (msg.error() and
                       msg.error().code() == confluent_kafka.KafkaError._PARTITION_EOF):

        logging.debug("No new message was received from broker.")

        # We return empty string as no message was readed.
        # Prometheus will get reponse with empty body
        return ""

    # we got different error than _PARTITION_EOF, we raise it
    if msg.error():
        logging.error("Get Kafka error {}".format(msg.error()))
        raise KafkaConsumptionException(msg.error())

    # we got proper message
    msg_str = msg.value().decode('utf-8')
    logging.debug("New message was received from broker:\n{}\n".format(msg_str))
    return msg_str


def http_get_handler(topic_name: str, kafka_broker_addresses: List[str],
                     group_id: str) -> (int, bytes):
    """Logic of HTTP GET handler slightly abstracted from
    used http server.

    Returns:
        tuple with 1) reponse code and 2) body (encoded into bytes)

    The logic is not put inside MetricsRequestHandler for sake of
    simpler testing the code. Testing http.server is not trivial
    and would need quite complex mocking.
    """
    if topic_name in kafka_consumers:
        kafka_consumer = kafka_consumers[topic_name]
        logging.debug('Reuse existing consumer {!r} for topic {!r}'.format(
            id(kafka_consumer), topic_name))
    else:
        kafka_consumer = create_kafka_consumer(kafka_broker_addresses, topic_name,
                                               group_id=group_id)
        kafka_consumers[topic_name] = kafka_consumer
        logging.info('Register new consumer {!s} for topic {!r}'.format(
            id(kafka_consumer), topic_name))

    response_code, body = "", ""
    try:
        msg = consume_one_message(kafka_consumer)
        response_code = 200
        if msg == '':
            msg = 'no_messages{topic="%s"} 1' % topic_name
    except KafkaConsumptionException as e:
        msg = str(e)
        response_code = 503
        logging.warning('Kafka execption: {!r}'.format(e))

    body = msg.encode('utf-8')
    return response_code, body


class MetricsRequestHandler(BaseHTTPRequestHandler):
    def __init__(
            self,
            topic_names,
            kafka_broker_addresses,
            group_id,
            request,
            client_address,
            server
            ):
        self.topic_names = topic_names
        self.kafka_broker_addresses = kafka_broker_addresses
        self.group_id = group_id
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handler for HTTP GET method. Reads one message from kafka.

        Consumes one, if available, message from kafka topic.
        Uses given in constructor kafka_consumer for
        accessing kafka.
        """
        topic_name = self.path.lstrip('/')
        if topic_name in self.topic_names:
            response_code, body = http_get_handler(
                topic_name, self.kafka_broker_addresses, self.group_id)
            self.send_response(response_code)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(body)
        else:
            # not found
            self.send_response(404, 'Topic not found!')
            self.end_headers()
            self.wfile.write(b'Topic not found!')

    # Suppress inf
    def log_request(self, *args, **kwargs):
        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            super().log_request(*args, **kwargs)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def run_server(ip: str, port: int, args) -> None:
    server_address = (ip, port)
    handler_class = partial(MetricsRequestHandler,
                            args.topic_names,
                            args.kafka_broker_addresses,
                            args.group_id,
                            )
    httpd = ThreadedHTTPServer(server_address, handler_class)
    httpd.serve_forever()
