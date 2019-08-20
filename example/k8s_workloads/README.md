## Node affinity

Load generators are only scheduled to nodes labeled with **goal="load_generator"**.
All "services" are only scheduled to nodes labeled with **goal="service"**.

### Example node configuration

```
kubectl label node node10 node12        goal=load_generator
kubectl label node node11 node13 node14 goal=service

kubectl label node node10 node12        memory=1lm
kubectl label node node11 node13 node14 memory=2lm
```



