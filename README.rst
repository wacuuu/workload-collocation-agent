==========================
RMI Kafka Consumer
==========================

Overview
============

A Kafka consumer which exposes the latest read message in its own HTTP server.
RMI stands for Resource Mesos Integration, see https://github.intel.com/serenity/rmi/.


Motivation
============

There is no official integration between Prometheus and Kafka and we need this funtionality in RMI project.
In RMI we send metrics already in Prometheus format to Kafka, so the only thing to done in this project is 
to read them and expose them in internal HTTP server to allow Prometheus to srap the data.


Requirements
============

- Python >= 3.6.x
