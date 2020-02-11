#!/bin/bash
echo "Waiting for halyard pod to be ready"

export KUBECONFIG=/home/vagrant/.kube/config

#while true
for i in {1..30} 
do
STATE=$(kubectl get po oes-spinnaker-halyard-0  -n oes -o jsonpath='{..containerStatuses..ready}')
if [ $STATE == "true" ]
  then
    echo "Halyard Pod is  ready"
    break
else
    echo "Waiting for Halyard to be ready"
    sleep 60
fi
done
