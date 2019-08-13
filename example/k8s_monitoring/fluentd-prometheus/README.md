sudo docker build --network=host  . -t 100.64.176.12:80/fluentd-prometheus
sudo docker push 100.64.176.12:80/fluentd-prometheus

sudo docker run -d --network=host -v $PWD/fluent.conf:/fluentd/etc/fluent.conf --name fluentd 100.64.176.12:80/fluentd-prometheus sleep 36000

curl 127.0.0.1:24231/metrics

