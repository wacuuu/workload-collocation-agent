Getting started
===============

You need to create dedicated `prometheus` namespace for operator.

To use prometheus operator with wca, Fluentd and Grafana use command in current dir:
```bash
kubectl create namespace prometheus
kubectl apply -f .
```
(make sure you run wca daemonset separately from `wca_daemonset` directory).

Access the Prometheus at:
some http://worker-node:30900/graph

and Grafana at:
some http://worker-node:32135

Note that, after deployment remember to add prometheus source in Grafana.
You can use prometheus service ClusterIP to set source in Grafana.

Example:

```bash
kubectl get svc -n prometheus prometheus

NAME         TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
prometheus   NodePort   10.233.6.244   <none>        9090:30900/TCP   164m

```

Then in Grafana:

```
URL: http://10.233.6.244:9090
Access: Server(default)
```
