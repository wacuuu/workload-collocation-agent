Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with name `node36`
- there is ``wca-scheduler`` namespace on cluster

kube-scheduler configuration
----------------------------

Add new policy as config map:

``kubectl apply -f scheduler-policy.yaml``

Give access to read configmaps for kube-scheduler:

``kubectl apply -f scheduler-policy-role.yaml``

Edit kube-scheduler pod manifest on master node (``/etc/kubernetes/manifests/kube-scheduler.yaml``) to use policy with external scheduler.

.. code-block:: yaml

        spec:
          containers:
          - command:
            ...
            - --policy-configmap=scheduler-policy
            - --policy-configmap-namespace=kube-system
   

wca-scheduler deployment
------------------------

Build wca-scheduler image with "100.64.176.12:80/wca-scheduler:latest" tag:

``docker build -t 100.64.176.12:80/wca-scheduler:latest -f examples/kubernetes/wca-scheduler/Dockerfile .``

Push image to repository:

``docker push 100.64.176.12:80/wca-scheduler:latest``

Apply wca-scheduler deployment:

``kubectl apply -k examples/kubernetes/wca-scheduler/``
