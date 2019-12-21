=============
wca-scheduler
=============

.. contents:: Table of Contents

**This software is pre-production and should not be deployed to production servers.**

Introduction
============
wca-scheduler extend kube-scheduler with algorithms.

Architecture
============
< picture >

Configuration
=============
wca-scheduler needs to provide configuration file.

Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with wca-scheduler static pod.

Prepare wca-scheduler pex file.

``make wca_scheduler_package``

Prepare docker image.

``make wca_scheduler_docker_image``

Push image to repository.

``docker tag wca-scheduler:latest 100.64.176.12:80/wca-scheduler:latest
``docker push 100.64.176.12:80/wca-scheduler:latest``

Prepare wca-scheduler service which expose ``31800`` port to communicate with wca-scheduler NGINX server.

``kubectl apply -f wca-scheduler-service.yaml``

Copy ``wca-scheduler-service.yaml`` to master node.

Let's assume that wca-scheduler pod manifest (``wca-scheduler-pod.yaml``) is in ``/etc/kubernetes/manifests`` directory for automatically pod serving.
