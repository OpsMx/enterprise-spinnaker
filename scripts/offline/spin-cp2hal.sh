#!/bin/bash
# Script to copy halyard files from Spinnaker offline computer to Halyard pod

#WORKDIR=$HOME/offlinespinnaker
export WORKDIR=$PWD
export OLROOT=$WORKDIR/airgapped-spin

# === Manual steps ===
# kubectl create ns offline
# cd /tmp; mkdir -p spin/hal spin/redis spin/minio; chmmod 777 spin
# kubectl apply -f spin-pv.yaml
# helm --debug install --set halyard.spinnakerVersion=local:1.16.1i \
#   --set halyard.image.tag=1.29.0,redis.image.pullPolicy=IfNotPresent \
#   spinnaker spinnaker-1.23.1.tgz -n offline --timeout 20m0s 
# ----

HAL=$(kubectl get pods | grep halyard-0 | awk '{print $1}')
kubectl exec -it $HAL -- bash -c 'mkdir -p /home/spinnaker/.kube /home/spinnaker/.hal'
kubectl cp ~/.kube/config  $HAL:/home/spinnaker/.kube/config
kubectl cp $OLROOT/spin-boms.tar.gz $HAL:/home/spinnaker/spin-boms.tar.gz
kubectl cp $OLROOT/spin-deployhal.sh $HAL:/home/spinnaker/spin-deployhal.sh

echo "DONE - Copying files to Halyard !!!"
