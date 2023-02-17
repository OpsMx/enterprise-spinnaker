# This Script download all pods logs in the given namespace
# and tar and gzip those files
#!/bin/bash
ns=$1
ISD_ADMIN_USERNAME=$2
ISD_ADMIN_PASSWORD=$3
REDIS_HOST=$4
REDIS_PORT=$5
REDIS_PASSWORD=$6
ISD_GATE_URL=$7
DAYS=$8
INSTALLATION_TYPE=$9
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
  containername=$(kubectl get po $podname -n $ns -o jsonpath='{.spec.containers[0].name}')
  echo getting logs for $podname
  kubectl -n $ns logs $podname -c $containername > logdir/"$podname".log
done < logdir/pods.txt
python3 extract_logs.py $ISD_ADMIN_USERNAME $ISD_ADMIN_PASSWORD $REDIS_HOST $REDIS_PORT $REDIS_PASSWORD $ISD_GATE_URL $DAYS $INSTALLATION_TYPE
zip -r -e "$filename.zip" logdir -P 'opsmx-password'
rm -rf logdir
echo please send /tmp/$filename.zip to opsmx by email
