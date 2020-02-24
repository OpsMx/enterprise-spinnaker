#!/bin/bash
echo "Waiting for halyard pod to be ready"

export KUBECONFIG=/home/vagrant/.kube/config

STATE=$(kubectl get po oes-spinnaker-halyard-0  -n oes -o jsonpath='{..containerStatuses..ready}')
if [ -z "$STATE" ]
then
      echo "Halyard Pod could not be found. Installation appears to have failed"
      exit 1
fi

#while true
for i in {1..30} 
do
STATE=$(kubectl get po oes-spinnaker-halyard-0  -n oes -o jsonpath='{..containerStatuses..ready}')
if [ $STATE == "true" ]
  then
    echo "Halyard Pod is  ready"
    exit 0
else
    echo "Waiting for Halyard to be ready..$i"
    sleep 60
fi
done
echo "Spinnaker halyard pod did not come-up in the specified time.Installation appears to have failed."
