sudo add-apt-repository -y ppa:vbernat/haproxy-1.9
sudo apt-get update
sudo apt-get install -y haproxy
sudo cp /vagrant/haproxy.cfg.sample /etc/haproxy/haproxy.cfg
sudo service haproxy restart
