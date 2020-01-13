Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with `kubernetes.io/hostname` = `node36`

kube-scheduler configuration
----------------------------

Apply wca-scheduler-policy config map:

``kubectl apply -f wca-scheduler-policy.yaml``

Give access to read configmaps for kube-scheduler:

``kubectl apply -f wca-scheduler-policy-role.yaml``

Edit kube-scheduler pod manifest (``/etc/kubernetes/manifests/kube-scheduler.yaml``) to use policy with external scheduler.

.. code-block:: yaml

        spec:
          containers:
          - command:
            ...
            - --policy-configmap=scheduler-policy
            - --policy-configmap-namespace=kube-system
   

wca-scheduler deployment
------------------------

Prepare docker image:

``docker build -t wca-scheduler:latest .``

Push image to repository:

``docker tag wca-scheduler:latest 100.64.176.12:80/wca-scheduler:latest``

``docker push 100.64.176.12:80/wca-scheduler:latest``

Check if wca-scheduler pod is running:

``kubectl apply -k .``
