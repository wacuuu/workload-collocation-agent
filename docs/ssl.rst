===============================
SSL (Secure Socket Layer)
===============================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

Introduction
------------

Secure Socket Layer allow to secure commucation trought components.


Configuration 
-------------

Example of minimal configuration that uses ``SSL``:

.. code:: yaml

    runner: !AllocationRunner
      node: !KubernetesNode
        cgroup_driver: cgroupfs

        # Fill needed PATH to key and certificate to access kubelet.
        ssl: !SSL
          server_verify: True
          client_cert_path: "$PATH/apiserver-kubelet-client.crt"
          client_key_path: "$PATH/apiserver-kubelet-client.key"
