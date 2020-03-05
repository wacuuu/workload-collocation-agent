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

Prepare docker image:

``docker build -t wca-scheduler:latest .``

Push image to repository:

``docker tag wca-scheduler:latest 100.64.176.12:80/wca-scheduler:latest``

``docker push 100.64.176.12:80/wca-scheduler:latest``

Check if wca-scheduler pod is running:

``kubectl apply -k .``


TLS connection of wca-scheduler with kube-scheduler
------------------------------------------------

TLS is required to secure a connection between wca-scheduler and kube-scheduler.

Instructions are based on https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/

The cfssl tools from https://pkg.cfssl.org/ are required to generate the private key and
to create a Certificate Signing Request (CSR) next.
More information about the tools: https://blog.cloudflare.com/introducing-cfssl/ .

After downloading and installing the cfssl tools, you can generate a private key and
Certificate Signing Request based on the private key.
In Certificate Signing Request the key ``hosts`` has two values.
``wca-scheduler.wca-scheduler.pod`` is pod's DNS name.
``100.64.176.36`` is example IP address, where wca-scheduler will be deployed.
You should change this IP address to address, where the wca-scheduler will be deployed.

.. code-block:: shell

    # Download the cfssl tools
    wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -O cfssljson
    wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -O cfssl
    sudo chmod u+x cfssljson cfssl

    # Generate a private key and CSR. Change IP address to wca-scheduler node address!
    cat << EOF | ./cfssl genkey - | ./cfssljson -bare server
    {
      "hosts": [
        "wca-scheduler.wca-scheduler.pod",
        "100.64.176.36"
      ],
      "CN": "wca-scheduler.wca-scheduler.pod",
      "key": {
        "algo": "ecdsa",
        "size": 256
      }
    }
    EOF

The next step is to create CSR Kubernetes object and send it to apiserver.
It contains previously created CSR.
Created Kubernetes CertificateSigningRequest must be approved.
It can be done by an automated approval process or by a cluster administrator.
Below script uses example certificate approved by the administrator.

.. code-block:: shell

    # Create CSR K8S object
    cat <<EOF | kubectl apply -f -
    apiVersion: certificates.k8s.io/v1beta1
    kind: CertificateSigningRequest
    metadata:
      name: wca-scheduler.wca-scheduler
    spec:
      request: $(cat server.csr | base64 | tr -d '\n')
      usages:
      - digital signature
      - key encipherment
      - server auth
    EOF

    # The CSR must be approved by administrator (or automated approval process)
    kubectl certificate approve wca-scheduler.wca-scheduler

Now, you can download the signed certificate.
When you have a set of the certificate and the private key, you can create Secret using them.
The Secret will be forwarded to wca-scheduler.

.. code-block:: shell

    # Download the Certificate
    kubectl get csr wca-scheduler.wca-scheduler -o jsonpath='{.status.certificate}' | base64 --decode > server.crt

    # Create Secret with the certificate and the private key
    kubectl create secret generic wca-scheduler-cert --from-file server.crt --from-file server-key.pem --namespace wca-scheduler
