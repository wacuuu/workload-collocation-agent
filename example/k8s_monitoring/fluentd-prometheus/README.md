sudo docker build --network=host  . -t 100.64.176.12:80/fluentd-prometheus
sudo docker push 100.64.176.12:80/fluentd-prometheus
