Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with wca-scheduler static pod.

Prepare wca-scheduler pex file:

``make wca_scheduler_package``

Prepare docker image:

``make wca_scheduler_docker_image``

Push image to repository:

``docker tag wca-scheduler:latest 100.64.176.12:80/wca-scheduler:latest``

``docker push 100.64.176.12:80/wca-scheduler:latest``

On kubernetes master node prepare service which expose ``31800`` port to communicate with wca-scheduler NGINX server

``kubectl apply -f wca-scheduler-service.yaml``

and copy ``wca-scheduler-pod.yaml`` to ``/etc/kubernetes/manifests`` where pods are automatically deployed.

Check if wca-scheduler pod is running:

``kubectl get pods -n kube-system``
