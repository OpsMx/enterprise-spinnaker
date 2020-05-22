cd /vagrant; mkdir -p pv-spin/halyard pv-spin/minio pv-spin/redis; chmod -R 777 pv-spin/
cd $HOME; kubectl apply -f spin-pv.yaml
cp -v priv-docker-reg.yml airgapped-spin/

cd airgapped-spin;
helm --debug install --set halyard.spinnakerVersion=local:1.17.2,halyard.image.tag=1.29.0, \
  --set halyard.additionalScripts.enabled=true,halyard.additionalScripts.configMapName=cm-spinnaker-boms, \
  --set halyard.additionalScripts.configMapKey=callCopyBoms.sh,redis.image.pullPolicy=IfNotPresent \
  --set minio.image.repository=10.168.3.10:8082/minio,halyard.image.repository=10.168.3.10:8082/halyard \
  --set redis.image.registry=10.168.3.10:8082,redis.image.repository=redis \
  --set gcs.enabled=false -f priv-docker-reg.yml spinnaker spinnaker-1.23.1.tgz -n offline \
  --timeout 20m0s | tee helminstall-docker1.log

