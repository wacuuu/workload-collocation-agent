#### Work in progess setup (TODO: move to serivce or using k8s operator)

Prometheus is run on **100.64.176.36** as root (using ```sudo tmux```)

form `/root/prometheus-2.11.0-rc.0.linux-amd64` run

```
./prometheus --config.file ./prometheus.yaml --web.enable-lifecycle --web.enable-admin-api --storage.tsdb.retention.time=15m --query.lookback-delta=30s
```
to reload config: 

```
sudo pkill -HUP prometheus
```


to check rules:
```
promtool check rules ./prometheus.rules.yaml && pkill -HUP prometheus
promtool check rules ./prometheus-apms.rules.yaml && pkill -HUP prometheus
```
