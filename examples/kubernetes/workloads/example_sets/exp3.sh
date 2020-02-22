echo ------------------------------



echo 1
date

workloads_set=3
zero_workloads_sleep=300
workloads_sleep=1600

kubectl scale sts --all --replicas=0;sleep $zero_workloads_sleep

./disable_extender.sh
./taint.sh
./workloads${workloads_set}.sh; sleep $workloads_sleep
kubectl scale sts --all --replicas=0;sleep $zero_workloads_sleep

echo 2
date

./untaint.sh
./workloads${workloads_set}.sh; sleep $workloads_sleep
kubectl scale sts --all --replicas=0;sleep $zero_workloads_sleep

echo 3
date

./enable_extender.sh
./workloads${workloads_set}.sh; sleep $workloads_sleep
kubectl scale sts --all --replicas=0;sleep $zero_workloads_sleep

# wait two more rounds
sleep $zero_workloads_sleep
sleep $zero_workloads_sleep

