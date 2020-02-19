#!/bin/bash
# K.Srinivas 5-Dec-2019
#Script to be executed on node1
#For creating PVs, PVCs and binding them
#Not sure which PVCs need to be created, but they should be in the help package
#################################################################################################################
### PLEASE UPDATE THESE WITH THE USERNAME AND CREDENTIALS provided by OpsMX
#################################################################################################################
DOCKER_USERNAME=''   # USER_NAME_GOES_HERE
DOCKER_PASSWORD=''   # PASSWORD_GOES_HERE
#################################################################################################################

if [[ -z "$DOCKER_USERNAME" || -z "$DOCKER_PASSWORD" ]]
then
   echo "ERROR:Docker Username and password must be updated in inst_oes.sh"
   exit 1
fi

export KUBECONFIG=/home/vagrant/.kube/config

#kubectl taint nodes $(hostname) node-role.kubernetes.io/master:NoSchedule-
kubectl create ns oes
kubectl create secret docker-registry oes-repo --docker-username=$DOCKER_USERNAME --docker-password=$DOCKER_PASSWORD --docker-email=opsmx@example.com --namespace oes
kubectl create secret generic my-kubeconfig -n oes --from-file=config=/vagrant/admin.conf

kubectl delete -f /vagrant/oes-pv.yaml  2>&1 > /dev/null
kubectl delete -f /vagrant/autopilot-pv.yaml  2>&1 > /dev/null
kubectl delete -f /vagrant/spin-gate-svc.yaml -n oes  2>&1 > /dev/null
kubectl delete clusterrolebinding oes-spinnaker-spinnaker 2>&1 > /dev/null

cd /home/vagrant
rm -rf PVDIR
mkdir -p PVDIR
mkdir -p PVDIR/LIB-POSTGRESQL
mkdir -p PVDIR/minio
mkdir -p PVDIR/redis
mkdir -p PVDIR/halyard
mkdir -p PVDIR/ELASTICSEARCH
chmod -R 777 PVDIR

# Create PVs as required

kubectl apply -f /vagrant/autopilot-pv.yaml
kubectl apply -f /vagrant/oes-pv.yaml
kubectl apply -f /vagrant/spin-gate-svc.yaml -n oes

rm -rf enterprise-spinnaker 2>&1 > /dev/null
git clone https://github.com/OpsMx/enterprise-spinnaker.git 
cd enterprise-spinnaker/charts/oes

echo "Installing OES using Helm, this make take 10-mins or more depending on the network and CPU speed"

# If you want to install Kibana based monitoring, please uncomment this line
#echo "/vagrant/helm install oes . --namespace oes --set enableCentralLogging=true"
#/vagrant/helm install oes . --namespace oes --set enableCentralLogging=true

# Comment this line if you want only OES without kibana
echo "/vagrant/helm install oes . --namespace oes "
/vagrant/helm install oes . --namespace oes 

exit 0

