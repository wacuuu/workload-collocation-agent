Getting started
===============

You need to create dedicated `prometheus` namespace for operator.

To use prometheus operator with wca, Fluentd and Grafana use command in current dir:
```bash
kubectl create namespace prometheus
kubectl apply -f .
```
(make sure you run wca daemonset separately from `wca_daemonset` directory).

After deployment remember to add prometheus source in Grafana.