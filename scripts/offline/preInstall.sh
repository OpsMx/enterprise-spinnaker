#!/bin/bash
scriptname=$(basename $BASH_SOURCE)

#Exit if Private Docker registry is not supplied
if [ $# -eq 0 ]; then
   echo "ERROR: Private Docker Regisry is not supplied"
   echo "Syntax: $scriptname <private-registry-url>"
   echo "Example: $scriptname 10.168.3.10:8082"

   exit 1
fi
DCR=$1

BOMCM=$(kubectl get cm | grep -i boms | awk '{print $1}')
echo $BOMCM
[ ! -z $BOMCM ] && kubectl delete cm cm-spinnaker-boms

WORKDIR=$PWD
cd $WORKDIR

#[ -s airgapped-spin/spin-boms.tar.gz ] && rm -fv airgapped-spin/spin-boms.tar.gz
#Change the below line to remove /vagrant
tar -xzvf airgapped-spin.tar.gz
cd airgapped-spin/
tar -xzvf spin-boms.tar.gz
mv spin-boms.tar.gz spin-boms.tar.gz_old
VFILE=$(ls .boms/bom/*.*.*.yml)
echo $VFILE
sed -i "s|dockerRegistry: .*|dockerRegistry: $DCR|" $VFILE
head -5 $VFILE
tar -cvzf spin-boms.tar.gz .boms

base64 spin-boms.tar.gz | base64 - > boms.enc
file spin-boms.tar.gz boms.enc
du spin-boms.tar.gz boms.enc

cat >callCopyBoms.sh <<-"EOF"
#!/bin/bash
#This Script is executed in using-Halyard Pod
#File path: /opt/halyard/additional/callCopyBoms.sh
#Dir /opt/halyard/additional/ owned by root. Script executed by spinnaker
echo -n "My host is :"; hostname
cd /tmp

cat >copyBoms.sh <<-"HALEOF"
#Purpose: Copies BOM files to /home/spinnaker/.hal/.boms
echo "This Host is :"
hostname; hostname -i
cd /tmp
CMBOM=$(kubectl get configmap | grep boms | awk '{print $1}')
kubectl get configmap $CMBOM -o "jsonpath={.data['boms\.enc']}" > boms.enc
cat boms.enc | base64 -d | base64 -d > spin-boms.tar.gz
du spin-boms.tar.gz boms.enc
tar -xzvf spin-boms.tar.gz
[ ! -d /home/spinnaker/.hal ] && mkdir -pv /home/spinnaker/.hal 
cp -rv .boms /home/spinnaker/.hal/
echo "DONE - BOM"
HALEOF

HAL=$(kubectl get pods | grep halyard-0 | awk '{print $1}')
#Disable Halyard to pull versions.yml from config www.googleapis.com bucket
kubectl exec $HAL -- bash -c "echo 'spinnaker.config.input.gcs.enabled: false' >> /opt/halyard/config/halyard-local.yml"
kubectl exec $HAL -- bash -c "hal shutdown && hal"
until $HAL_COMMAND --ready; do sleep 10 ; done
chmod +x copyBoms.sh
kubectl cp copyBoms.sh $HAL:/tmp/copyBoms.sh
kubectl exec $HAL -- bash -c "/tmp/copyBoms.sh"
EOF
kubectl create configmap cm-spinnaker-boms --from-file=./boms.enc --from-file=./callCopyBoms.sh
