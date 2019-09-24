Getting started
===============

Files in this folder will deploy:

- **fluentd** for APMs metrics
- **grafana** for visualization
- **prometheus** using (prometheus-opearator) with custom rules for metrics collection, storage and 
  evaluation
- **wca** as daemonset (on nodes marked with label goal=service)

1. You need to create dedicated namespaces for those applications like this:

```shell
kubectl create -f namespaces.yaml
```

2. Create hostPath based directory as grafana volume.

```shell 
# on master node
sudo mkdir /var/lib/grafana
sudo chown o+rw /var/lib/grafana
```

Grafana is deployed on master and hostPath as volume at accessible `/var/lib/grafana`

3. Uusing kustomize (-k) deploy all applications:

```shell
kubectl apply -k .
```

Note: in case of 

`unable to recognize ".": no matches for kind "Prometheus" in version "monitoring.coreos.com/v1"` 

warnings, please run `kubectl apply -k .` once again. This is a problem of invalid order of objects
when CRDs are created by kustomize and prometheus-operator.

You can check progress of deployment using `kubectl get -k .`.

# Access

**Prometheus** is exposed at: http://worker-node:30900/graph

**Grafana** is exposed at: http://worker-node:32135

Note that, after deployment remember to add prometheus source in Grafana.

```
URL: http://prometheus.prometheus:9090
Access: Server(default)
```

## Grafana configuration (addons)

### Grafana boomtable plugin

Required for 2LM contention demo:

https://grafana.com/grafana/plugins/yesoreyeram-boomtable-panel

Grafana is deployed on master and hostPath as volume at accessible `/var/lib/grafana`

```shell 
kubectl exec --namespace grafana -ti `kubectl get pod -n grafana -oname --show-kind=false | cut -f 2 -d '/'` bash
grafana-cli plugins install yesoreyeram-boomtable-panel
# restart 
kubectl delete -n grafana `kubectl get pod -n grafana -oname`
```

### Configuring Kubernetes-app for Grafana

Manually import dashboards from `grafana/dashboards`.

### Configuring Kubernetes-app for Grafana

Parameters:

- URL: https://100.64.176.36:6443
- TLS Client Auth: checked
- With CA Cert: checked

```shell
# CA cert
kubectl config view --raw -ojsonpath="{@.clusters[0].cluster.certificate-authority-data}" | base64 -d
# Client cert
kubectl config view --raw -ojsonpath="{@.users[0].user.client-certificate-data}" | base64 -d
# Client key
kubectl config view --raw -ojsonpath="{@.users[0].user.client-key-data}" | base64 -d
```

# Troubleshooting

### Access WCA and fluentd

Both applications are running in **host** network namespace as daemonsets on ports:

- **WCA** : http://worker-node:9100
- **Fluentd** : http://worker-node:24231

### Cleaning up

**Warning!**: this removes all the objects (excluding CRDs and namespaces)

```shell
bash cleanup.sh

kubectl delete namespace fluentd
kubectl delete namespace grafana
kubectl delete namespace prometheus
kubectl delete namespace wca
```

### Remove namespace if stuck in "Terminating" state

**Warning!**: there might be orphaned resources left after that

```shell
kubectl proxy &
for NS in fluentd grafana prometheus wca; do
kubectl get namespace $NS -o json | sed '/kubernetes/d' | curl -k -H "Content-Type: application/json" -X PUT --data-binary @- 127.0.0.1:8001/api/v1/namespaces/$NS/finalize
done
```

### Service Monitor configuration

https://github.com/coreos/prometheus-operator/blob/master/Documentation/troubleshooting.md#L38

### Missing metrics from node_exporter (e.g. node_cpu)

This setup uses new version of node_exporter (>18.0) and Grafana kubernetes-app is based on old naminch scheme 
from node_exporter v 0.16
Prometheus rules "16-compatibilit-rules-new-to-old" are used to configured new evaluation rules from backward compatibility.

