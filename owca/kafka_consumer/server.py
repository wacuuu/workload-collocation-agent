from functools import partial
from typing import List, Dict
import threading
import logging
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer

import confluent_kafka


logging.getLogger('').setLevel('DEBUG')


class KafkaConsumptionException(Exception):
    """Error while reading data from kafka topic."""
    pass


TopicName = str
kafka_consumers: Dict[TopicName, confluent_kafka.Consumer] = {}
# We use List instaed of collections.deque as
#   thanks to that we do not need to use threading.Lock (GIL and list atomic operations),
#   memory and performance gains are marginal for
#   our usage (small containers sizes).
most_recent_buffers: Dict[TopicName, List] = {}


def create_kafka_consumer(broker_addresses: List[str],
                          topic_name: str,
                          group_id: str) -> confluent_kafka.Consumer:
    consumer = confluent_kafka.Consumer({
        'bootstrap.servers': ",".join(broker_addresses),
        'group.id': group_id,
    })
    consumer.subscribe([topic_name])
    return consumer


def create_kafka_consumers(
        broker_addresses: List[str],
        topic_names: List[str],
        group_id: str) -> None:
    kafka_consumers.clear()
    for topic_name in topic_names:
        kafka_consumers[topic_name] = create_kafka_consumer(
            broker_addresses, topic_name, group_id)
        logging.info('Register new consumer {!s} for topic {!r}'.format(
            id(kafka_consumers[topic_name]), topic_name))


def consume_one_message(kafka_consumer: confluent_kafka.Consumer, timeout=0) -> str:
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
    msg = kafka_consumer.poll(timeout=timeout)

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


def append_with_max_size(buf, N, msg):
    """Appends new element and keeps N with the highest indexes. defined for N > 0"""
    # Optimilization would be to implement ring buffer instead.
    assert N > 0
    if N == 1:
        buf_copy = []
    else:
        buf_copy = buf[-N+1:]
    buf_copy.append(msg)
    return buf_copy


def consume_messages_to_most_recent_buffer(topic_name, timeout, most_recent_count):
    """Thread target to consume messages in a loop."""
    kafka_consumer = kafka_consumers[topic_name]
    while True:
        try:
            msg = consume_one_message(kafka_consumer, timeout)
            if msg != '':
                logging.debug('%s adding msg: %r', topic_name, msg)
                most_recent_buffers[topic_name] = append_with_max_size(
                    most_recent_buffers[topic_name], most_recent_count, msg)
        except KafkaConsumptionException as e:
            msg = str(e)
            logging.warning('Kafka exception: {!r}'.format(e))


def http_get_handler(topic_name: str, kafka_broker_addresses: List[str],
                     group_id: str, is_most_recent_mode: bool) -> (int, bytes):
    """Logic of HTTP GET handler slightly abstracted from
    used http server.

    :param is_most_recent_mode: in "most_recent mode" consume messages in seperate threads,
        otherwise consume synchronously in this function.

    Returns:
        tuple with 1) reponse code and 2) body (encoded into bytes)

    The logic is not put inside MetricsRequestHandler for sake of
    simpler testing the code. Testing http.server is not trivial
    and would need quite complex mocking.
    """
    response_code, body = "", ""

    if not is_most_recent_mode:
        try:
            msg = consume_one_message(kafka_consumers[topic_name])
            response_code = 200
            if msg == '':
                msg = 'no_messages{topic="%s"} 1' % topic_name
        except KafkaConsumptionException as e:
            msg = str(e)
            response_code = 503
            logging.warning('Kafka execption: {!r}'.format(e))
    else:
        # thread-safe way of cloning a list in CPython
        buf_copy = most_recent_buffers[topic_name][:]
        msg = "\n".join(buf_copy)
        response_code = 200

    body = msg.encode('utf-8')
    return response_code, body


class MetricsRequestHandler(BaseHTTPRequestHandler):
    def __init__(
            self,
            topic_names,
            kafka_broker_addresses,
            group_id,
            is_most_recent_mode,
            request,
            client_address,
            server
            ):
        self.topic_names = topic_names
        self.kafka_broker_addresses = kafka_broker_addresses
        self.group_id = group_id
        self.is_most_recent_mode = is_most_recent_mode
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
                topic_name, self.kafka_broker_addresses,
                self.group_id, self.is_most_recent_mode)
            self.send_response(response_code)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            try:
                self.wfile.write(body)
            except BrokenPipeError as e:
                logging.warn(
                    "BrokenPipeError Exception was raised while trying to\n"
                    "\twrite to socket. It is probably not dangerous and means\n"
                    "\tthat client sending http request stopped to wait\n"
                    "\tfor an answer.")
            except ConnectionResetError as e:
                logging.warn("ConnectionResetError was raised.")
            except Exception as e:
                logging.warn("Exception {} was raised".format(e))
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
                            args.most_recent_count > 0)

    create_kafka_consumers(
        broker_addresses=args.kafka_broker_addresses,
        topic_names=args.topic_names, group_id=args.group_id)

    if args.most_recent_count > 0:
        # Infinite timeout:
        #   https://github.com/confluentinc/confluent-kafka-python/
        #       blob/master/confluent_kafka/src/Consumer.c#L887
        timeout = -1
        for topic_name in args.topic_names:
            most_recent_buffers[topic_name] = []
            t = threading.Thread(
                target=consume_messages_to_most_recent_buffer,
                args=(topic_name, timeout, args.most_recent_count))
            t.start()

    httpd = ThreadedHTTPServer(server_address, handler_class)
    httpd.serve_forever()
