# K.Srinivas 5-Dec-2019
#Script to be executed on node1
#For creating PVs, PVCs and binding them
#Not sure which PVCs need to be created, but they should be in the help package
#################################################################################################################
### PLEASE UPDATE THESE WITH THE USERNAME AND CREDENTIALS provided by OpsMX
#################################################################################################################
DOCKER_USERNAME=<username>
DOCKER_PASSWORD=<password>
#################################################################################################################

kubectl create ns oes
kubectl create secret docker-registry oes-repo --docker-username=$DOCKER_USERNAME --docker-password=$DOCKER_PASSWORD --docker-email=opsmx@example.com --namespace oes

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

kubectl apply -f /vagrant/oes-pv.yaml
kubectl apply -f /vagrant/autopilot-pv.yaml
kubectl apply -f /vagrant/spin-gate-np.yaml -n oes

rm -rf enterprise-spinnaker
git clone https://github.com/OpsMx/enterprise-spinnaker.git 
cd enterprise-spinnaker/charts/oes
echo "Installing OES using Helm, this make take 10-mins or depending on the network and CPU speed"
echo "/vagrant/helm install oes . --namespace oes --set enableCentralLogging=true"
/vagrant/helm install oes . --namespace oes 
#/vagrant/helm install oes . --namespace oes --set enableCentralLogging=true
