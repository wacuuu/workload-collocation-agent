
# https://pkg.cfssl.org/
wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64 -O cfssljson
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64 -O cfssl
sudo chmod u+x cfssljson cfssl

cat <<EOF | microk8s.kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mypod
  labels:
    app: myapp
spec:
  containers:
  - name: myapp-container
    image: ubuntu
    command: ['sh', '-c', 'echo Hello Kubernetes! && sleep 3600000']
    volumeMounts:
      - name: wca-scheduler-certs
        mountPath: /var/run/secrets/kubernetes.io/certs

  volumes:
    - name: wca-scheduler-certs
      configMap:
        name: wca-scheduler-certs
EOF

cat <<EOF | ./cfssl genkey - | ./cfssljson -bare server
{
  "hosts": [
    "wca-scheduler.default.svc.cluster.local",
    "wca-scheduler.default.pod.cluster.local",
    "10.91.126.122"
  ],
  "CN": "wca-scheduler.default.pod.cluster.local",
  "key": {
    "algo": "ecdsa",
    "size": 256
  }
}
EOF

cat <<EOF | microk8s.kubectl apply -f -
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

microk8s.kubectl certificate approve wca-scheduler.default

microk8s.kubectl get csr wca-scheduler.default -o jsonpath='{.status.certificate}' \
    | base64 --decode > server.crt

microk8s.kubectl create secret generic wca-scheduler-certs-2 --from-file server.crt --from-file server-key.pem
