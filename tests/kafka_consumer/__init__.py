# There is a name collision between tests/kafka_consumer/test_server.py and tests/test_server.py
# Apparently adding __init__.py file fixes it while removing all the *.pyc files found inside
# the project - does not.
