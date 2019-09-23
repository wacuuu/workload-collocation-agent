echo -------------------------------- FLUENTD --------------------------------------------------
kubectl delete serviceaccount --all -n fluentd
kubectl delete ds --all -n fluentd
kubectl delete cm --all -n fluentd
kubectl delete svc --all -n fluentd
kubectl delete rolebinding --all -n fluentd
kubectl delete role --all -n fluentd
kubectl delete servicemonitor.monitoring.coreos.com/fluentd -n fluentd
kubectl api-resources --verbs=list --namespaced -o name | grep -v events | xargs -n 1 kubectl get --show-kind --ignore-not-found -n fluentd


echo ---------------------------------- GRAFANA -------------------------------------------------------------------
kubectl delete deploy --all -n grafana
kubectl delete svc --all -n grafana
kubectl delete cm --all -n grafana
kubectl delete rolebinding --all -n grafana
kubectl delete role --all -n grafana

kubectl api-resources --verbs=list --namespaced -o name | grep -v events | xargs -n 1 kubectl get --show-kind --ignore-not-found  -n grafana

echo ---------------------------------- PROMETHEUS ------------------------------------------------------------------
kubectl delete deploy --all -n prometheus
kubectl delete sts --all -n prometheus
kubectl delete serviceaccount --all -n prometheus
kubectl delete svc --all -n prometheus
kubectl delete cm --all -n prometheus
kubectl delete rolebinding --all -n prometheus
kubectl delete role --all -n prometheus
kubectl api-resources --verbs=list --namespaced -o name | grep -v events | xargs -n 1 kubectl get --show-kind --ignore-not-found  -n prometheus
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl get customresourcedefinitions

echo ------------------------------------ WCA ----------------------------------------------------------------
kubectl delete ds --all -n wca
kubectl delete serviceaccount --all -n wca
kubectl delete svc --all -n wca
kubectl delete cm --all -n wca
kubectl delete rolebinding --all -n wca
kubectl delete role --all -n wca
kubectl delete servicemonitor.monitoring.coreos.com/wca -n wca
kubectl api-resources --verbs=list --namespaced -o name | grep -v events | xargs -n 1 kubectl get --show-kind --ignore-not-found  -n wca


echo ------------------------------------ Cluster scoped roles and bindings ----------------------------------------------------------------
kubectl delete clusterrolebinding prometheus
kubectl delete clusterrole prometheus
kubectl delete clusterrolebinding prometheus-operator
kubectl delete clusterrole prometheus-operator
kubectl delete clusterrolebinding fluentd
kubectl delete clusterrole fluentd
kubectl delete clusterrolebinding wca
kubectl delete clusterrole wca

