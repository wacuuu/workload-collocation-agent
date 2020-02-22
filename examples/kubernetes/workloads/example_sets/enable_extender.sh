kubectl -n wca-scheduler scale deployment wca-scheduler --replicas=1 ; sleep 5; kubectl get pods -n wca-scheduler
