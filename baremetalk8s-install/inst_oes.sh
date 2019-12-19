# K.Srinivas 5-Dec-2019
#Script to be executed on node1
#For creating PVs, PVCs and binding them
#Not sure which PVCs need to be created, but they should be in the help package

kubectl create ns oes
kubectl create secret docker-registry oes-repo --docker-username=USERNAME --docker-password=PASSWORD --docker-email=opsmx@example.com --namespace oes

#CHANGE THIS AS REQUIRED
cd /home/vagrant

rm -rf PVDIR
mkdir -p PVDIR
mkdir -p PVDIR/LIB-POSTGRESQL
mkdir -p PVDIR/minio
mkdir -p PVDIR/redis
mkdir -p PVDIR/halyard
chmod -R 777 PVDIR

#CHANGE THIS AS REQUIRED
cd /vagrant

# Create PVs as required
kubectl apply -f oes-pv.yaml
kubectl apply -f autopilot-pv.yaml

git clone https://github.com/OpsMx/enterprise-spinnaker.git 
cd enterprise-spinnaker/charts/oes
helm install oes . --namespace oes --set enableCentralLogging=true
