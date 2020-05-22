#!/bin/bash
# Script to push Docker images from tar files to private registry
scriptname=$(basename $BASH_SOURCE)

#Exit if version is not supplied. Version format is x.y.z
if [ $# -eq 0 ]; then
   echo "ERROR: Private Docker Regisry is not supplied"
   echo "Syntax: $scriptname <private-registry-url>"
   echo "Example: $scriptname 10.168.3.10:8082"
   exit 1
fi
DCR=$1

TOOLS=true
(command -v docker > /dev/null 2>&1) || { echo "ERROR: docker is not found."; TOOLS=false; }
(command -v tee > /dev/null 2>&1) || { echo "ERROR: tee is not found."; TOOLS=false; }

if [ $TOOLS != true ]; then
   echo "Make sure the required CLI tools are available and try again"
   exit 1
fi

#OL in variables mean OffLine
#WORKDIR=$HOME/offlinespinnaker
WORKDIR=$PWD
OLROOT=$WORKDIR/airgapped-spin

#Untar the airgapped spinnaker all-in-one file
echo "Untarring airgapped-spin.tar.gz" 
#tar -xzvf airgapped-spin.tar.gz 

cd $OLROOT
echo "Untarring spin-images.tar.gz" 
#tar -xzvf spin-images.tar.gz 

IMGFILE=$WORKDIR/dockerload.log
cat /dev/null > $IMGFILE
echo "Loading Docker images from spin-images/ directory"
for x in spin-images/*.tar; do
  echo "-- $x"
  sudo  docker load -i $x | tee -a $IMGFILE
done

echo "DONE - Docker Load !!!"

echo "Pushing Docker images to private registry"
while IFS= read -r line; do
   echo "$line"
   REG_IMG=$(echo $line | awk '{print $3}')
   IMG=$(basename $REG_IMG)
   PRIV_IMG=$DCR/$IMG
   echo $REG_IMG
   echo $IMG
   echo $PRIV_IMG
   sudo docker tag $REG_IMG $PRIV_IMG
   sudo docker push $PRIV_IMG
   sudo docker rmi -f $REG_IMG
   sudo docker rmi -f $PRIV_IMG
done < $IMGFILE

echo "DONE - Docker Load & Push!!!"

