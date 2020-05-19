#!/bin/bash
# Script to prepare Spinnaker BOM files

# In the target Spinnaker halyard, the BOM files should go to ~/.hal/.boms
# Version file is at .boms/bom/1.10.1.yml
# Component files are at .boms/<component>/<component-version>
# If Component version files are not available, then default is used from ~/.hal/.boms/<component>/<component>.yml
scriptname=$(basename $BASH_SOURCE)

#Exit if version is not supplied. Version format is x.y.z
if [ $# -eq 0 ]; then
    echo "ERROR: Spinnaker version is not supplied"
    echo "Syntax: $scriptname <ver>"
    exit 1
fi
VER=$1

TOOLS=true
(command -v yq > /dev/null 2>&1) || { echo "Error: yq is not found."; TOOLS=false; }
(command -v gsutil > /dev/null 2>&1) || { echo "Error: gsutil is not found."; TOOLS=false; }
(command -v svn > /dev/null 2>&1) || { echo "Error: svn (subversion) CLI is not found."; TOOLS=false; }
(command -v docker > /dev/null 2>&1) || { echo "Error: docker is not found."; TOOLS=false; }

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

mkdir -p $SRCROOT; cd $SRCROOT

# Download BOM version file. This is the base for driving the rest of the script
[ ! -s $TMPFILE ] && wget -O $TMPFILE https://storage.googleapis.com/halconfig/bom/$VER.yml

mkdir -p $BOMSROOT/bom
cp -vf $TMPFILE $FILE
#gsutil cp gs://halconfig/bom/$VER.yml $FILE

#Pull BOM files
declare -a services=$(yq r $TMPFILE services | egrep -v ' .*|monit' | sed 's/:$//')
for x in ${services[@]}; do
  echo 
  xver=$(yq r $TMPFILE services.$x.version)
  echo -e "== $x \t: $xver"
  mkdir -p $BOMSROOT/$x
  gsutil -m cp -R gs://halconfig/$x/$xver/* $BOMSROOT/$x/
done
echo
 
#Additionally download the Rosco depeding packer files
cd $BOMSROOT/rosco/
svn checkout https://github.com/spinnaker/rosco/trunk/rosco-web/config/packer
sudo rm -r ./packer/.svn
cd ./packer
wget https://raw.githubusercontent.com/spinnaker/rosco/master/rosco-web/config/rosco.yml
cd $SRCROOT

#Update component version with local: prefix
sed -i -e  '/commit/{n;s/version: /version: local:/;}' $FILE
#Update Spinnaker version with local: prefix
sed -i "s/^version: /version: local:/" $FILE

echo "Creating $SRCROOT/spin-boms.tar.tz"
tar -cvzf spin-boms.tar.gz .boms 

echo "DONE - Spinnaker BOM !!!"
