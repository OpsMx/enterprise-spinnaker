#Install Virtual Box 5.2
echo "deb http://download.virtualbox.org/virtualbox/debian bionic contrib" | tee -a /etc/apt/sources.list
wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | apt-key add -
wget -q https://www.virtualbox.org/download/oracle_vbox.asc -O- | apt-key add -
apt-get update
apt-get install virtualbox-5.2

#Install Vagrant
wget https://releases.hashicorp.com/vagrant/2.2.4/vagrant_2.2.4_linux_amd64.zip
unzip vagrant_2.2.4_linux_amd64.zip
mv vagrant /usr/bin
chmod 755 /usr/bin/vagrant
rm -f vagrant_2.2.4_linux_amd64.zip


Install helm 3.0.1
wget https://get.helm.sh/helm-v3.0.1-linux-amd64.tar.gz
tar -xvf helm-v3.0.1-linux-amd64.tar.gz
mv linux-amd64/helm /usr/bin
chmod 755 /usr/bin/helm
cp /usr/bin/helm .
rm -rf linux-amd64 helm-v3.0.1-linux-amd64.tar.gz

vagrant plugin install vagrant-disksize

# Printout all the version
echo "###############################################################"
echo "###############################################################"
echo "Version of Virtual Box"
vboxmanage --version
echo "###############################################################"
echo "Version of Vagrant"
vagrant version
echo "###############################################################"
echo "Version of helm"
helm version
echo "###############################################################"
echo "Software set up completed"
echo "###############################################################"
echo "###############################################################"



