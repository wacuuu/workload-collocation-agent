kubectl -n wca-scheduler scale deployment wca-scheduler --replicas=0 ; sleep 1; kubectl get pods -n wca-scheduler
