cp /vagrant/hosts /etc/hosts
sysctl -w net.ipv4.ip_forward=1
apt-get update && apt-get install -y apt-transport-https ca-certificates curl software-properties-common

### Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

### Add Docker apt repository.
add-apt-repository \
  "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) \
  stable"

## Install Docker CE.
apt-get update && apt-get install -y docker-ce=18.06.2~ce~3-0~ubuntu

# Setup daemon.
cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF

mkdir -p /etc/systemd/system/docker.service.d

# Restart docker.
systemctl daemon-reload
systemctl restart docker

apt-get install -y  ebtables ethtool 
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
#Add the kubernetes repo to your system.
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF
apt-get update
K8S_VERSION=1.15.2-00
K8S_CNI_VERSION=0.7.5-00
apt-get install -y kubelet=$K8S_VERSION kubectl=$K8S_VERSION kubeadm=$K8S_VERSION kubernetes-cni=$K8S_CNI_VERSION --allow-unauthenticated
echo "Sleeping for a minute..."
sleep 60
/vagrant/kubeadm_join_cmd.sh

cd /home/vagrant
mkdir .kube
cp /vagrant/admin.conf .kube/config
chown vagrant:vagrant .kube/config
cp /vagrant/bashrc /home/vagrant/.bashrc
chown vagrant:vagrant .bashrc
