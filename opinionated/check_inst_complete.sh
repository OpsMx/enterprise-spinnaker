#!/bin/bash
echo "Waiting for all Spinnaker Services to come-up"

export KUBECONFIG=/home/vagrant/.kube/config

CLOUD=false
DECK=false
ECHO=false
FRONT=false
GATE=false
IGOR=false
ORCA=false
ROSCO=false

for i in {1..20}
do
kubectl get po -n oes -o jsonpath='{range .items[*]}{..metadata.name}{"\t"}{..containerStatuses..ready}{"\n"}{end}' > /tmp/inst.status
CLOUD=$(grep spin-cloud /tmp/inst.status | awk '{print $2}')
DECK=$(grep spin-deck /tmp/inst.status | awk '{print $2}')
ECHO=$(grep spin-echo /tmp/inst.status | awk '{print $2}')
FRONT=$(grep spin-front /tmp/inst.status | awk '{print $2}')
GATE=$(grep spin-gate /tmp/inst.status | awk '{print $2}')
IGOR=$(grep spin-igor /tmp/inst.status | awk '{print $2}')
ORCA=$(grep spin-orca /tmp/inst.status | awk '{print $2}')
ROSCO=$(grep spin-rosco /tmp/inst.status | awk '{print $2}')

if [ "$CLOUD" == "true" ] && [ "$DECK" == "true" ] && [ "$ECHO" == "true" ] && [ "$FRONT" == "true" ] && [ "$GATE" == "true" ] && [ "$IGOR" == "true" ] && [ "$ORCA" == "true" ] && [ "$ROSCO" == "true" ]
  then
    echo "Spinnaker is ready"
    break
else
    echo "Waiting for Spinnaker to be ready"
    sleep 60
fi
done

echo "==========================================================================="
echo "==========================================================================="
echo 
echo "Installation of Spinnaker is now complete. Login to the URL below using admin/OpsMx@123"
echo 
kubectl get svc spin-deck-ui -n oes -o jsonpath='{"http://10.168.3.10:"}{..nodePort}{"\n"}'
echo 
echo "==========================================================================="
echo "==========================================================================="
