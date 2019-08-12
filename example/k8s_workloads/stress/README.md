sudo docker build --network=host  . -t 100.64.176.12:80/stress-ng-apm
sudo docker push 100.64.176.12:80/stress-ng-apm:latest
