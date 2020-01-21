# OpsMx: Temporary fix for a bug in Spin-Deck+Docker env.
# Should not be used in Production
export KUBECONFIG=/home/vagrant/.kube/config
REP_STR="      securityContext:\n        runAsUser: 0"
kubectl get deploy spin-deck -n oes -o yaml > /tmp/spin-deck.yaml
sed -e "s/^      securityContext: {}/$REP_STR/1"  < /tmp/spin-deck.yaml > /tmp/spin-deck-fixed.yaml
kubectl apply -f /tmp/spin-deck-fixed.yaml
