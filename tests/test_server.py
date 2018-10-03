# Important note:
# do not create real objects of confluent_kafka.Consumer class:
# it may result in stucking tests (waiting on confluent_kafka internal
# threads to be finished).
# For reference look at how confluent_kafka.Consumer is mocked in test function
# test_http_get_handler__success.

from functools import partial
import pytest
from unittest import mock

from confluent_kafka import KafkaError

from owca_kafka_consumer.server import (consume_one_message,
                                        KafkaConsumptionException,
                                        create_kafka_consumer,
                                        create_kafka_consumers,
                                        http_get_handler,
                                        append_with_max_size)


# To not pass to each call to below two functions parameter kafka_poll_timeout
#   partials are created with the same names as originals.
consume_one_message = partial(consume_one_message)
kafka_broker_addresses = ['127.0.0.1']
group_id = 'test-group'
topic_name = 'testing-topic'

http_get_handler = partial(http_get_handler, topic_name=topic_name,
                           kafka_broker_addresses=kafka_broker_addresses,
                           group_id=group_id, is_most_recent_mode=False)


# Creating mock confluent_kafka.Consumer inline
#   in decorator mock.patch is not quite readeable
#   so below are three functions to create mocked
#   classes aimed at different test cases
def create_consumer_mock__consumed(message_value):
    """Successfully consumed one message."""
    error_fun = mock.Mock(return_value=False)
    value_fun = mock.Mock(return_value=message_value)
    message = mock.Mock(error=error_fun, value=value_fun)
    poll = mock.Mock(return_value=message)
    Consumer = mock.Mock(poll=poll)
    return Consumer


def create_consumer_mock__timeout():
    """Timeout on poll function."""
    message = mock.Mock(return_value=None)
    poll = mock.Mock(return_value=message)
    Consumer = mock.Mock(poll=poll)
    return Consumer


def create_consumer_mock__error_code(error_code):
    """Error while consuming data."""
    code_fun = mock.Mock(code=mock.Mock(return_value=error_code))
    error_fun = mock.Mock(return_value=code_fun)
    message = mock.Mock(error=error_fun)
    poll = mock.Mock(return_value=message)
    Consumer = mock.Mock(poll=poll)
    return Consumer


MSG_VAL = "Message".encode('utf-8')  # in bytes


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=create_consumer_mock__consumed(MSG_VAL))
def test_consume_one_message__consumed(mock_kafka_consumer):
    kafka_consumer = create_kafka_consumer(["any"], "any", "any")
    msg = consume_one_message(kafka_consumer)
    assert msg == MSG_VAL.decode('utf-8')


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=mock.Mock(poll=mock.Mock(return_value=None)))
def test_consume_one_message__timeout(mock_kafka_consumer):
    """Timeout on reading from kafka -- return message is None."""
    kafka_consumer = create_kafka_consumer(["any"], "any", "any")
    msg = consume_one_message(kafka_consumer)
    assert msg == ""


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=create_consumer_mock__error_code(KafkaError._PARTITION_EOF))
def test_consume_one_message__error_partition_eof(mock_kafka_consumer):
    """_PARTITION_EOF is special exceptional case: we do not differ it from timeout.
    See consume_one_message docstring."""
    kafka_consumer = create_kafka_consumer(["any"], "any", "any")
    msg = consume_one_message(kafka_consumer)
    assert msg == ""


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=create_consumer_mock__error_code(KafkaError._UNKNOWN_PARTITION))
def test_consume_one_message__error_unknown_partition(mock_kafka_consumer):
    """Any error code different than _PARTITION_EOF; here _UNKNOWN_PARTITION."""
    kafka_consumer = create_kafka_consumer(["any"], "any", "any")
    with pytest.raises(KafkaConsumptionException):
        consume_one_message(kafka_consumer)


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=create_consumer_mock__consumed(MSG_VAL))
def test_http_get_handler__success(*mock):
    create_kafka_consumers(["None"], [topic_name], "None")
    assert http_get_handler() == (200, MSG_VAL)


@mock.patch('owca_kafka_consumer.server.confluent_kafka.Consumer',
            return_value=create_consumer_mock__error_code(KafkaError._UNKNOWN_PARTITION))
def test_http_get_handler__error(*mock):
    create_kafka_consumers(["None"], [topic_name], "None")
    assert http_get_handler()[0] == 503


def test_append_with_max_size():
    buf = [1, 2, 3, 4, 5]
    msg = 6
    assert append_with_max_size(buf, 3, msg) == [4, 5, 6]
    assert append_with_max_size(buf, 1, msg) == [6]
    assert append_with_max_size(buf, 10, msg) == [1, 2, 3, 4, 5, 6]
