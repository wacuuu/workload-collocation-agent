# Installation

```sh
# after upload to /home/ppalucki/wca_remote_pycharm
sudo ln -vfs ~/wca_remote_pycharm/example/k8s_scheduler/kube-scheduler.yaml /etc/kubernetes/manifests/kube-scheduler.yaml
sudo ln -vfs ~/wca_remote_pycharm/example/k8s_scheduler/scheduler-policy.json /etc/kubernetes/scheduler-policy.json
sudo journalctl -u kubelet -f
```