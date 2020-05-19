#!/bin/bash
# Script to download and save Spinnaker services' Docker imagess

scriptname=$(basename $BASH_SOURCE)

#Exit if version is not supplied. Version format is x.y.z
if [ $# -eq 0 ]; then
   echo "ERROR: Spinnaker version is not supplied"
   echo "Syntax: $scriptname <ver>"
   exit 1
fi
VER=$1

TOOLS=true
(command -v docker > /dev/null 2>&1) || { echo "ERROR: docker is not found."; TOOLS=false; }
(command -v curl > /dev/null 2>&1) || { echo "ERROR: curl is not found."; TOOLS=false; }

if [ $TOOLS != true ]; then
   echo "Make sure the required CLI tools are available and try again"
   exit 1
fi

#OL in variables mean OffLine
#WORKDIR=$HOME/offlinespinnaker
WORKDIR=$PWD
SRCROOT=$WORKDIR/offlinesrc
BOMSROOT=$SRCROOT/.boms
FILE=$BOMSROOT/bom/$VER.yml
TMPFILE=$SRCROOT/spin-ver.yml

[ ! -d $SRCROOT ] && mkdir -p $SRCROOT; cd $SRCROOT

# Download BOM version file. This is the base for driving the rest of the script
[ ! -s $TMPFILE ] && wget -O $TMPFILE https://storage.googleapis.com/halconfig/bom/$VER.yml

mkdir spin-images
declare -a services=$(yq r $TMPFILE services | egrep -v ' .*|monit' | sed 's/:$//') 

#Pull Docker images
echo "PULL DOCKER IMAGES"
mkdir spin-images
for x in ${services[@]}; do
  echo 
  xver=$(yq r $TMPFILE services.$x.version)
  echo -e "== $x \t: $xver"
  sudo docker pull gcr.io/spinnaker-marketplace/$x:$xver
done
echo 
#Pull other dependent services' docker images
sudo docker pull docker.io/bitnami/redis:4.0.11-debian-9
sudo docker pull minio/minio:RELEASE.2018-08-25T01-56-38Z
sudo docker pull gcr.io/spinnaker-marketplace/halyard:1.29.0

#Save Docker images
echo "SAVE DOCKER IMAGES"
for x in ${services[@]}; do
  echo 
  xver=$(yq r $TMPFILE services.$x.version)
  echo -e "== $x \t: $xver"
  sudo docker save gcr.io/spinnaker-marketplace/$x:$xver -o spin-images/$x.tar
  echo 
done
#Save other dependent services' docker images
sudo docker save docker.io/bitnami/redis:4.0.11-debian-9 -o spin-images/redis.tar
sudo docker save minio/minio:RELEASE.2018-08-25T01-56-38Z -o spin-images/minio.tar
sudo docker save gcr.io/spinnaker-marketplace/halyard:1.29.0 -o spin-images/halyard.tar

echo "Creating $SRCROOT/spin-images.tar.gz"
sudo chown -R $(id -u):$(id -g) spin-images
tar -czvf spin-images.tar.gz spin-images

echo "DONE - Docker Save !!!"
