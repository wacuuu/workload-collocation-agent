==========================
OWCA Kafka Consumer
==========================

Overview
============

A Kafka consumer which exposes the latest read message in its own HTTP server.
OWCA stands for Orchestration-aware Workload Collocation Agent, see https://github.intel.com/serenity/owca/.


Motivation
============

There is no official integration between Prometheus and Kafka and we need this
funtionality in OWCA project.  In OWCA we send metrics already in Prometheus
format to Kafka, so the only thing developed in this project is to read them and
expose them using HTTP server to allow Prometheus to scrap the data.


Requirements
============

- Python >= 3.6.x
