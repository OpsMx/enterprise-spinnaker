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

apt-get install -y ebtables ethtool 
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
#Add the kubernetes repo to your system.
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb http://apt.kubernetes.io/ kubernetes-xenial main
EOF

apt-get update
K8S_VERSION=1.15.2-00
K8S_CNI_VERSION=0.7.5-00
apt-get install -y kubelet=$K8S_VERSION kubectl=$K8S_VERSION kubeadm=$K8S_VERSION kubernetes-cni=$K8S_CNI_VERSION --allow-unauthenticated
IP_ADDR=10.168.3.10
kubeadm init --apiserver-advertise-address=$IP_ADDR --apiserver-cert-extra-sans=$IP_ADDR  --node-name master --pod-network-cidr=10.244.0.0/16
kubectl taint nodes master node-role.kubernetes.io/master:NoSchedule-
kubectl apply  --kubeconfig=/etc/kubernetes/admin.conf -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version --kubeconfig=/etc/kubernetes/admin.conf | base64 | tr -d '\n')&env.IPALLOC_RANGE=10.244.0.0/16"

cd /home/vagrant
mkdir .kube
cp /etc/kubernetes/admin.conf .kube/config
cp /etc/kubernetes/admin.conf /vagrant
chown vagrant:vagrant .kube/config
cp /vagrant/bashrc .bashrc

kubectl taint nodes $(hostname) node-role.kubernetes.io/master:NoSchedule-  --kubeconfig=/etc/kubernetes/admin.conf
