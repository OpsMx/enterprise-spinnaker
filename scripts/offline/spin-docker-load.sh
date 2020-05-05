#!/bin/bash
# Script to load Docker images from tar files

TOOLS=true
(command -v docker > /dev/null 2>&1) || { echo "ERROR: docker is not found."; TOOLS=false; }

if [ $TOOLS != true ]; then
   echo "Make sure the required CLI tools are available and try again"
   exit 1
fi

#OL in variables mean OffLine
#WORKDIR=$HOME/offlinespinnaker
WORKDIR=$PWD
OLROOT=$WORKDIR/airgapped-spin
SRCROOT=$WORKDIR/offlinesrc
BOMSROOT=$SRCROOT/.boms
FILE=$BOMSROOT/bom/$VER.yml
TMPFILE=$SRCROOT/spin-ver.yml

#Untar the airgapped spinnaker all-in-one file
echo "Untarring airgapped-spin.tar.gz" 
tar -xzvf airgapped-spin.tar.gz 

cd $OLROOT
echo "Untarring spin-images.tar.gz" 
tar -xzvf spin-images.tar.gz 

echo "Loading Docker images from spin-images/ directory"
for x in spin-images/*.tar; do
  echo "-- $x"
  sudo  docker load -i $x
done

echo "DONE - Docker Load !!!"
