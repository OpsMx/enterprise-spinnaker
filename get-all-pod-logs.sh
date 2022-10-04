# This Script download all pods logs in the given namespace
# and tar and gzip those files
#!/bin/bash
ns=$1
[ -z "$ns" ] && echo "Please pass namespace as an argument"
[ -z "$ns" ] && exit 1
FILE=logs.tar            
NAME=${FILE%.*}
EXT=${FILE#*.} 
DATE=`date +%d-%m-%Y-%H-%M-%S`         
filename=${NAME}-${DATE}.${EXT}
echo $filename
echo getting logs from $ns
cd /tmp
rm -rf logdir
rm -rf logs*.tar.gz
mkdir -p logdir
kubectl get po -n $ns --no-headers > logdir/pods.txt
while read -r line;
do
  podname=$(echo "$line" | awk '{print$1}')
  echo getting logs for $podname
  kubectl -n $ns logs $podname > logdir/"$podname".log
done < logdir/pods.txt
tar -cvf $filename logdir
gzip $filename
rm -rf logdir
echo please send /tmp/$filename.gz to opsmx by email