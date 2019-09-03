### DEBUGGING

```bash
kubectl delete ds --all -n monitoring ; kubectl delete cm --all -n monitoring
kubectl apply -k . -n monitoring ; k -n monitoring rollout status ds fluentd
while sleep 1 ; do kubectl -n monitoring logs --tail 5 --follow `kubectl get pods -owide -n monitoring |grep node14 | awk '{print $1}'`; done
curl 100.64.176.40:24231/metrics
```


