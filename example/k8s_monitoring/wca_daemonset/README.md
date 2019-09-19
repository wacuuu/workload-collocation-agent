Getting started
===============


1. Build image

```
make wca_package_in_docker

# Grab the name of create image like: wca-{commit}
# e.g. wca-4fd64bc3f61dc0afc8247c0c25adba2fc8af9a55
docker tag wca-4fd64bc3f61dc0afc8247c0c25adba2fc8af9a55:latest 100.64.176.12:80/wca:latest
docker push 100.64.176.12:80/wca:latest

```


To run wca in deamonset use `kubectl apply -f .` in current directory.