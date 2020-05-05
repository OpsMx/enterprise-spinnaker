#!/bin/bash
# Script to prepare Spinnaker offline package including BOM files, Docker images

scriptname=$(basename $BASH_SOURCE)
scriptdir=$(cd `dirname $BASH_SOURCE` && pwd)

#Exit if version is not supplied. Version format is x.y.z
if [ $# -eq 0 ]; then
    echo "ERROR: Spinnaker version is not supplied"
    echo "Syntax: $scriptname <ver>"
    exit 1
fi
VER=$1

#OL in variables mean OffLine
#WORKDIR=$HOME/offlinespinnaker
export WORKDIR=$PWD
export OLROOT=$WORKDIR/airgapped-spin
export SRCROOT=$WORKDIR/offlinesrc
export BOMSROOT=$SRCROOT/.boms
export FILE=$BOMSROOT/bom/$VER.yml
export TMPFILE=$SRCROOT/spin-ver.yml

[ ! -d $OLROOT ] && mkdir -p $OLROOT
[ ! -d $SRCROOT ] && mkdir -p $SRCROOT; cd $SRCROOT
# Download BOM version file. This is the base for driving the rest of the script
wget -O $TMPFILE https://storage.googleapis.com/halconfig/bom/$VER.yml
cp -vf $TMPFILE $OLROOT/

# Download BOM files
cd $scriptdir; echo -e "\n\n-----> spin-getbom.sh"
bash $scriptdir/spin-getbom.sh $VER
mv -v $SRCROOT/spin-boms.tar.gz $OLROOT/

# Download Docker images
cd $scriptdir; echo -e "\n\n-----> spin-getbom.sh"
bash $scriptdir/spin-docker-save.sh $VER
mv $SRCROOT/spin-images.tar.gz $OLROOT/

#Download Helm chart
echo -e "\n\n-----> Fetching Spinnaker Helm chart"
cd $OLROOT; curl -O https://kubernetes-charts.storage.googleapis.com/spinnaker-1.23.1.tgz

#Create tar file from $OLROOT directory
echo "Creating $WORKDIR/airgapped-spin.tar.gz"
cd $WORKDIR/..
tar -czvf airgapped-spin.tar.gz airgapped-spin

echo "All-in-one file $WORKDIR/airgapped-spin.tar.gz is ready. Use this file for your offline installation"

echo "DONE - ALL !!!"
