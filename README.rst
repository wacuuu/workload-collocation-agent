==========================
RMI Kafka Consumer
==========================

Overview
============

A Kafka consumer which exposes the latest read message in its own HTTP server.
RMI stands for Resource Mesos Integration, see https://github.intel.com/serenity/rmi/.


Motivation
============

There is no official integration between Prometheus and Kafka and we need this
funtionality in RMI project.  In RMI we send metrics already in Prometheus
format to Kafka, so the only thing developed in this project is to read them and
expose them using HTTP server to allow Prometheus to scrap the data.


Requirements
============

- Python >= 3.6.x


Scenarios
============

1. Experiment name: read historical data not older than N minutes by prometheus.
   Assumptions:
       a. N < 5 minutes (prometheus does not allow to insert data with a timestamp
          "older" than few minutes)
       b. There is a kafka topic with unread metrics being ordered by timestamp.
       c. RMI-Kafka-Consumer is not running before the experiment starts.
       d. Kafka broker and prometheus are running before and throughout the experiment.
   Experiment:
       a. Run RMI-Kafka-Consumer for
       (count_of_messages_within_last_N_minutes/
        prometheus_scrape_interval_in_seconds) seconds
   Expected end state:
       a. Prometheus should accept all data from last N minutes.
