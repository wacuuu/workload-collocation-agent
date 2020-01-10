Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with `kubernetes.io/hostname` = `node36`

Prepare docker image:

``docker build -t wca-scheduler:latest -f examples/kubernetes/wca-scheduler/Dockerfile .``

Push image to repository:

``docker tag wca-scheduler:latest 100.64.176.12:80/wca-scheduler:latest``

``docker push 100.64.176.12:80/wca-scheduler:latest``

Check if wca-scheduler pod is running:

``kubectl apply -k -f examples/kubernetes/wca-scheduler/``
