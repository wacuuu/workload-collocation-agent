
```
git clone https://github.com/ColinIanKing/stress-ng
cd stress-ng
cp $PROJECT/examples/k8s_worklods/stress/{apm.patch, Dockerfile} .
make
```

```sh
sudo docker build --network=host  . -t 100.64.176.12:80/stress-ng-apm
sudo docker push 100.64.176.12:80/stress-ng-apm:latest
```
