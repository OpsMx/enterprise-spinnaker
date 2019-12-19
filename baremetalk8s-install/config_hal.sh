BASEURL=http://35.209.174.56:8181/jenkins
USERNAME=JENKINS_USERNAME
PASSWORD=JENKINS_PASSWORD
TOKEN_FILE=GITHUB-TOKEN

cd /vagrant
rm tmp-hal-config.sh
cat <<EOF >> /tmp/tmp-hal-config.sh
#!/bin/sh
hal config security ui edit --override-base-url http://10.168.3.11:32470
hal config security api edit --override-base-url http://10.168.3.11:32467
hal config provider kubernetes account add OpsMx-k8s --provider-version v2 --kubeconfig-file=/home/spinnaker/.kube/config --only-spinnaker-managed true
hal config provider kubernetes enable
hal config artifact github account add OpsMx-k8s-Github --token-file /home/spinnaker/.hal/$TOKEN_FILE
hal config artifact github enable

hal config ci jenkins master add OpsMx-k8s-Jenkins --address $BASEURL --username $USERNAME --password $PASSWORD
hal config ci jenkins enable

hal config security authn ldap edit --user-dn-pattern="cn={0}" --url=ldap://oes-openldap:389/dc=example,dc=org
hal config security authn ldap enable

hal deploy apply
EOF

chmod +x tmp.sh

kubectl cp ~/.kube/config oes-spinnaker-halyard-0:/home/spinnaker/.kube  -n oes
kubectl cp $TOKEN_FILE oes-spinnaker-halyard-0:/home/spinnaker/.hal  -n oes
kubectl cp /tmp/tmp-hal-config.sh oes-spinnaker-halyard-0:/home/spinnaker/tmp.sh  -n oes
kubectl exec oes-spinnaker-halyard-0 -n oes -- /home/spinnaker/tmp.sh
