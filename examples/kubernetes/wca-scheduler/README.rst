Example deployment
==================
Lets assume that:

- ``100.64.176.12`` - is node with docker image repository.
- ``100.64.176.36`` - is kubernetes master node with label `kubernetes.io/hostname` = `node36`

kube-scheduler configuration
----------------------------

Add new policy as config map:

``kubectl apply -f scheduler-policy.yaml``

Give access to read configmaps for kube-scheduler:

``kubectl apply -f scheduler-policy-role.yaml``

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


SSL connection
--------------



.. code-block:: shell
    # https://pkg.cfssl.org/
    wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -O cfssljson
    wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -O cfssl
    sudo chmod u+x cfssljson cfssl

    cat <<EOF | ./cfssl genkey - | ./cfssljson -bare server
    {
      "hosts": [
        "wca-scheduler.wca-scheduler.pod",
        "100.64.176.35"
      ],
      "CN": "wca-scheduler.wca-scheduler.pod",
      "key": {
        "algo": "ecdsa",
        "size": 256
      }
    }
    EOF

    cat <<EOF | kubectl apply -f -
    apiVersion: certificates.k8s.io/v1beta1
    kind: CertificateSigningRequest
    metadata:
      name: wca-scheduler.default
    spec:
      request: $(cat server.csr | base64 | tr -d '\n')
      usages:
      - digital signature
      - key encipherment
      - server auth
    EOF

    kubectl certificate approve wca-scheduler.default

    kubectl get csr wca-scheduler.default -o jsonpath='{.status.certificate}' | base64 --decode > server.crt

    kubectl create secret generic wca-scheduler-cert --from-file server.crt --from-file server-key.pem --namespace wca-scheduler
