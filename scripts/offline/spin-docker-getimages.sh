#OL in variables mean OffLine
#WORKDIR=$HOME/offlinespinnaker
WORKDIR=$PWD
SRCROOT=$WORKDIR/offlinesrc
BOMSROOT=$SRCROOT/.boms
FILE=$BOMSROOT/bom/$VER.yml
TMPFILE=$SRCROOT/spin-ver.yml

[ ! -d $SRCROOT ] && mkdir -p $SRCROOT; cd $SRCROOT

IMGFILE=$WORKDIR/image-overrides.yml
echo "Pulling Custom Docker images"
#Sample $line
#Loaded image: gcr.io/spinnaker-marketplace/deck:2.13.2-20191117034416

[ ! -d spin-images ] && mkdir spin-images

#Ignore commented lines in the $IMGFILE
sed '/^ *#/d;s/#.*//' $IMGFILE > $IMGFILE.tmp

while IFS= read -r line; do
   echo "$line"
   #Sample $line
   #gate: docker.io/devopsmx/ubi8-oes-gate:version-1.14.0
   #First field, removed the trailing colon (:)
   MSVC=$(echo $line | awk '{print $1}' | sed 's|\(^.*\):$|\1|')
   echo $MSVC
   REG_IMG=$(echo $line | awk '{print $2}')
   IMG=$(basename $REG_IMG)
   IMG_NAME=$(echo $IMG | awk -F ':' '{print $1}')
   IMG_TAG=$(echo $IMG | awk -F ':' '{print $2}')
   #PRIV_IMG=$DCR/$IMG
   echo $REG_IMG
   #echo $IMG
   #echo $IMG_NAME
   #echo $IMG_TAG
   sudo docker pull $REG_IMG
   sudo docker save $REG_IMG -o spin-images/$IMG_NAME.tar
   echo ----
done < $IMGFILE.tmp

echo "DONE - Docker Image Pull !!!"

