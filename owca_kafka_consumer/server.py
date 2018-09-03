"""
Reads one message from the queue while handling request;
single threaded (otherwise we could get out of order error in prometheus)
"""

from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from typing import List

import confluent_kafka


class KafkaConsumptionException(Exception):
    """Error while reading data from kafka topic."""
    pass


def consume_one_message(kafka_consumer: confluent_kafka.Consumer,
                        kafka_poll_timeout: float) -> str:
    """read one message from kafka consumer

    Args:
        timeout: consumer will wait for a message
        for maximum timeout seconds

    Raises:
        KafkaConsumptionException if there was any error
            reading data from kafka (note: the case where
            there is no new message to read from kafka
            is not exceptional condition - no exception is
            raised then)
    """
    msg = kafka_consumer.poll(kafka_poll_timeout)

    # https://docs.confluent.io/current/clients/
    #    confluent-kafka-python/index.html#confluent_kafka.Consumer.poll
    #
    # * msg == None if we got timeout on poll
    # * msg.error().code() == KafkaError._PARTITION_EOF when there is
    #   no new messages (kafka responded within timeout period)
    if msg is None or (msg.error() and
                       msg.error().code() == confluent_kafka.KafkaError._PARTITION_EOF):

        logging.info("No new message was received from broker.")

        # We return empty string as no message was readed.
        # Prometheus will get reponse with empty body
        return ""

    # we got different error than _PARTITION_EOF, we raise it
    if msg.error():
        logging.error("Get Kafka error {}".format(msg.error()))
        raise KafkaConsumptionException(msg.error())

    # we got proper message
    msg_str = msg.value().decode('utf-8')
    logging.info("New message was received from broker:\n{}\n"
                 .format(msg_str))
    return msg_str


def http_get_handler(kafka_consumer: confluent_kafka.Consumer,
                     kafka_poll_timeout: float) -> (int, bytes):
    """Logic of HTTP GET handler slightly abstracted from
    used http server.

    Returns:
        tuple with 1) reponse code and 2) body (encoded into bytes)

    The logic is not put inside MetricsRequestHandler for sake of
    simpler testing the code. Testing http.server is not trivial
    and would need quite complex mocking.
    """
    response_code, body = "", ""
    try:
        msg = consume_one_message(kafka_consumer, kafka_poll_timeout)
        response_code = 200
    except KafkaConsumptionException as e:
        msg = str(e)
        response_code = 503
    body = msg.encode('utf-8')
    return response_code, body


class MetricsRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, kafka_consumer, kafka_poll_timeout,
                 request, client_address, server):
        """
        Args:
            kafka_consumer (confluent_kafka.Consumer): Object used for
                access to kafka.
            kafka_poll_timeout: meaning defined in function consume_one_message
        """
        self.kafka_consumer = kafka_consumer
        self.kafka_poll_timeout = kafka_poll_timeout
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handler for HTTP GET method. Reads one message from kafka.

        Consumes one, if available, message from kafka topic.
        Uses given in constructor kafka_consumer for
        accessing kafka.
        """
        response_code, body = http_get_handler(self.kafka_consumer, self.kafka_poll_timeout)
        self.send_response(response_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(body)


def run_server(ip: str, port: int, kafka_consumer: confluent_kafka.Consumer,
               kafka_poll_timeout: float) -> None:
    server_address = (ip, port)
    handler_class = partial(MetricsRequestHandler, kafka_consumer, kafka_poll_timeout)
    httpd = HTTPServer(server_address, handler_class)
    httpd.serve_forever()


def create_kafka_consumer(broker_addresses: List[str],
                          topic_name: str,
                          group_id: str) -> confluent_kafka.Consumer:
    consumer = confluent_kafka.Consumer({
        'bootstrap.servers': ",".join(broker_addresses),
        'group.id': group_id,
    })
    consumer.subscribe([topic_name])
    return consumer
