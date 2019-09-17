Getting started
===============

To use prometheus operator with wca, Fluentd and Grafana use command in current dir:
```bash
kubectl apply -f .
```
(make sure you run wca daemonset separately from `wca_daemonset` directory).

After deployment remember to add prometheus source in Grafana.