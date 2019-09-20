Getting started
===============


1. Build image

```
make REPO=100.64.176.12:80 wca_docker_devel
and push to your 
sudo docker push 100.64.176.12:80/wca:devel
```


To run wca in deamonset use `kubectl apply -f .` in current directory.