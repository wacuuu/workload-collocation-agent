Getting started
===============

To run wca in deamonset: 

1. Build image

```
make REPO=100.64.176.12:80 wca_docker_devel
and push to your 
sudo docker push 100.64.176.12:80/wca:devel
```


2. (optionally) Overwrite image name to your local repository in kustomization.yaml

```yaml
...
# kustomization.yaml
images:
  - name: wca
    newName: REPO/wca
    newTag: devel
```

3. (optionally) Choose (**disable the default goal=service**) nodes to deploy owca using node selector

```yaml
# daemonset.yaml
spec:
    node-selector:
        kubernetes.io/hostname: node12

```

3. Create namespace

```shell
kubectl create namespace wca
```

4. Deploy wca (using kustomize)

```shell
kubectl apply -k .
```
