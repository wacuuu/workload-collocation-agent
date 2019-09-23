Getting started
===============

Files in this folder will deploy:

- **fluentd** for APMs metrics
- **grafana** for visualization
- **prometheus** using (prometheus-opearator) with custom rules for metrics collection, storage and 
  evaluation
- **wca** as daemonset (on nodes marked with label goal=service)

You need to create dedicated namespaces for those applications like this:

```shell
kubectl create -f namespaces.yaml
```

and then (using kustomize)  deploy all applications:

```shell
kubectl apply -k .
```

Note: in case of 

`unable to recognize ".": no matches for kind "Prometheus" in version "monitoring.coreos.com/v1"` 

warnings, please run `kubectl apply -k .` once again. This is a problem of invalid order of objects
when CRDs are created by kustomize and prometheus-operator.

# Access

**Prometheus** is exposed at: http://worker-node:30900/graph

**Grafana** is exposed at: http://worker-node:32135

Note that, after deployment remember to add prometheus source in Grafana.

```
URL: http://prometheus.prometheus:9090
Access: Server(default)
```


# Troubleshooting

### Access WCA and fluentd

Both applications are running in host network namespace as daemonsets on ports:

**WCA** : http://worker-node:9100
**Fluentd** : http://worker-node:24231



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
kubectl get namespace fluentd -o json | sed '/kubernetes/d' | curl -k -H "Content-Type: application/json" -X PUT --data-binary @- 127.0.0.1:8001/api/v1/namespaces/fluentd/finalize
kubectl get namespace grafana -o json | sed '/kubernetes/d' | curl -k -H "Content-Type: application/json" -X PUT --data-binary @- 127.0.0.1:8001/api/v1/namespaces/grafana/finalize
kubectl get namespace prometheus -o json | sed '/kubernetes/d' | curl -k -H "Content-Type: application/json" -X PUT --data-binary @- 127.0.0.1:8001/api/v1/namespaces/prometheus/finalize
kubectl get namespace wca -o json | sed '/kubernetes/d' | curl -k -H "Content-Type: application/json" -X PUT --data-binary @- 127.0.0.1:8001/api/v1/namespaces/wca/finalize
```


