sudo apt-get remove -y --purge virtualbox* 
sudo rm ~/"VirtualBox VMs" -Rf
sudo rm ~/.config/VirtualBox/ -Rf

rm -rf /opt/vagrant
rm -f /usr/bin/vagrant
rm -f /usr/bin/helm
rm -rf ~/.vagrant.d

echo "###############################################################"
echo "###############################################################"
echo "Software remove completed"
echo "###############################################################"
echo "###############################################################"

