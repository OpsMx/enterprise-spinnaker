#!/bin/bash
# Script to copy halyard files from Spinnaker offline computer to Halyard pod

cd $HOME
cd .hal
tar -xzvf ../spin-boms.tar.gz 

cat spinnaker.config.input.gcs.enabled: false >> /opt/halyard/config/halyard-local.yml


echo "DONE - Copying files to Halyard !!!"
