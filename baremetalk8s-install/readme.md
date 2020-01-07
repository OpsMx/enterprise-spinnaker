# Installing Open Enterprise Spinnaker (OES) on baremetal kubernetes

Most of the documentation available on in the internet assumes that we
are installing Spinnaker on GCP, Azure or some other cloud. However,
when we install Spinnaker on baremetal kubernetes, e.g. on-prem k8s
cluster, there are couple of challenges that we need to overcome:

- Lack of "automatically provisioned" Persistent Storage (Persistent
Volumes)

- Lack of "automatically provisioned" load-balancer

Steps to overcome these challenges are presented along with some
commonly used spinnaker configuration steps so to get a fairly
functional Spinnaker up and running.

In this blog, we see what these challenges are and how we can easily
overcome them. I will present 2 "levels" of solutions:

PART-I : Simple and "it works" : IP-address and Port-numbers are visible
in URLs. We also have a scripted install procedure that should work in
most cases and get you a functional Spinnaker in under an hour.

PART-II: Better-looking, handle more load: Handle more network load and
can be made to look like a part of an existing web-site.

To follow the steps mentioned here, you will need access to a kubernetes
cluster. Alternatively, you can install a master and worker-node using
vagrant scripts by following the **Scripted Installation** steps below.

Before going through the installation steps, its a great idea to go
through the following:

https://blog.opsmx.com/open-enterprise-spinnaker/ and

https://github.com/OpsMx/enterprise-spinnaker/tree/master/charts/oes

Also, all the files mentioned in this blog can be downloaded as follows:

**git clone** <https://github.com/ksrinimba/enterprise-spinnaker.git>

cd enterprise-spinnaker/baremetalk8s-install

Note: All instructions are tested on a laptop running Ubuntu 18.04,
vagrant(version2.2.4) created k8s (v15.2) nodes run Ubuntu 16.04 and
helm v3.0.1. The following scripts are available in the git repo, which
need to be edited, as appropriate, before executing:

**Requirements For Manual Installation:**

(I)Select a machine that has kubectl installed and kubeconfig pointing
to the target k8s cluster:

We use helm to install OES. Instructions for installing helm3 are here:

> [[https://helm.sh/docs/intro/install/]{.underline}](https://helm.sh/docs/intro/install/)

(II)Before you install OES, **please send an email to
[[spinnaker-poc\@opsmx.io]{.underline}](mailto:spinnaker-poc@opsmx.io)**
requesting access to the OES images. We would require your dockerhub id
to grant you access. If you do not already have a dockerhub id, you can
get one at [https://hub.docker.com](https://hub.docker.com/) .

**Scripted Installation**

Detailed step-by-step instuctions are available in the next section. The
instructions below install Kubernetes and configure Spinakar for common
use cases, all with-in an hour. These steps have been tested on
Vagrant-based installation on a Ubuntu 18.04 Machine with 32GB Memory
and 500GB Hard disk.

**Common Tasks :**

1\) Create a temporary directory and CD into it

2\) git clone <https://github.com/ksrinimba/enterprise-spinnaker.git>

3\) cd enterprise-spinnaker/baremetalk8s-install \# Stay in this
directory for subsequent steps

4\) Edit config\_hal.sh and update the usernames and passwords as
required

**Installation:**

A\) Open a terminal (ctrl+alt+T) and install virtualbox 5.2 from
[[here]{.underline}](https://qiita.com/shaching/items/4fcc95f20cff2450aa8f).

B\) Install Vagrant version2.2.4 from
[[here]{.underline}](https://linuxize.com/post/how-to-install-vagrant-on-ubuntu-18-04).

C\) Install disksize plugin for vagrant: vagrant plugin install
vagrant-disksize

D\) vagrant up \# Create VMs and install k8s master and node1 (10-15
minutes)

E\) vagrant ssh node1 \# ssh into node1

F\) /vagrant/inst\_oes.sh \# execute the script to install OES in k8s
(10 minutes)

Note: "Error: failed post-install: timed out waiting for the condition"
is normal as the installation takes longer

G\) Wait for installtion to complete. If required apply the fix
TIP-SPIN-DECK mentioned in detailed steps below

H\) /vagrant/config\_hal.sh \# Configure HAL (10 minutes)

I\) kubectl get svc spin-deck-ui -n oes -o
jsonpath=\'{\"http://10.168.3.11:\"}{\...nodePort}{\"\\n\"}\'

J\) Access Spinnaker URL (printed above) on your machine (Login with
<admin/OpsMx@123>, if required)

**Detailed Step-by-Step Installation**

a\) Create a namespace for our installation. In this example, its
**oes**.

kubectl create ns oes

b\) Create docker secret for installing OES add-ons such as Autopilot,
an AI based canary-deployment solution that allows production-grade
deployments with confidence.

kubectl create secret docker-registry oes-repo
\--docker-username=your\_username \--docker-password=your\_password
\--docker-email=opsmx\@example.com \--namespace oes

c\) Get the OpsMx Enterprise Spinnaker and change to the target
directory

git clone https://github.com/OpsMx/enterprise-spinnaker.git

cd enterprise-spinnaker/charts/oes

d\) Install OES using helm-3

helm install oes . \--namespace oes \--set enableCentralLogging=true

At this stage, helm installation will HANG as there are no persistent
volumes. Leave this command as is. It may "fail" as it times out after
sometime. That is ok. **In another window:**

e\) Check the PVCs that have been created. Overall, 3 PVCs need to be
satisfied for spinnaker to continue running and 1 PVC for Autopilot.

kubectl get pvc -n oes

f\) Create PersistentVolumes as given below. In this example, we are
using **hostPath** type PersistentVolumes. However, using an NFS-server
based PersistentVolumes are very similar and if possible, a better
option. Of course, we can also use cloud-storage options but why are we
on-prem if we are ok to put our data on cloud?

\(1\) Create the directories that will serve as Persistent Volume
stores.

> hostPath.path: This path refers to a directory that must exist and is
> writable by everyone. As an example:
>
> cd /home/vagrant \# Change this to the root-directory of your Storage
>
> mkdir -p PVDIR/LIB-POSTGRESQL \# Autopilot DB
>
> mkdir -p PVDIR/minio \# Minio, an S3 combatible DB used by Spinnaker
>
> mkdir -p PVDIR/redis \# Redis-cache
>
> mkdir -p PVDIR/halyard \#Halyard, the spinnaker "controller" home
> directory is mounted her
>
> chmod -R 777 PVDIR \# Make the target directores writable by all.

\(2\) Edit the following file (available as oes-pv.yaml from git) and
update:

\- hostPath.path to the one created above

\- namespace, if you are using a different namespace

\(3\) Create the PVs. Don't worry if k8s will schedule the pods to the
same nodes where the hostPath-PVs are created\...the scheduler is
intelligent to do it right :)

kubectl apply -f oes-pv.yaml \# PVs are not name-spaced

kubectl apply -f autopilot-pv.yaml \# In case you are installing
Autopilot as well

g\) After creating the PVs, give k8s a min or two for the PVCs to be
bound to the PVs:

kubectl get pvc -n oes

![](.//media/image1.png){width="6.6930555555555555in"
height="0.6520833333333333in"}

**TIPs:**

\(1\) If PVs and PVCs are NOT bound, Key points to remember:

A\) Check the name-space and pvc-name in the "claimRef" section of the
PVs. Note that PVCs are namespaced but PVs are not.

B\) "storageClass" should not be specified, unless you know what you are
doing. If you insist on specifying storageClass, it should match between
the PV and PVC you are expecting to bind. StorageClass object should
exist.

C\) If you make any changes to the claimRef section, you can simple
update it by:

kubectl apply -f oes-pv.yaml (or the appropriate file)

D\) Once a change is made, please give a minute or two before checking
if the PVC is bound to the PV.

E\) If there was a failed or partially successful binding, please DELETE
the PV and recreate it as the "Retain" policy may interfere with the
binding process when used 2^nd^ time.

F\) Finally, for any given PVC, you can check what is being requested by
using this command:

kubectl get pvc -n oes \<pvc-name\> -o yaml

and the PV offered using:"

kubectl get pv \<pv-name\> -o yaml

and ensure that PV and PVCs match exactly w.r.t:

\- AccessMode

\- Size (PV needs to be \>= PVC)

\- Delete any other qualifiers, worst case including the "claimRef"
section.

\(2\) If minio keeps going into CrashLoop, check the path and
permissions of the directory defined in the PV. It must be writable by
the minio-pod

\(3\) In case of PODs Crash for no apparent reason, please note that
after multiple tries, there may be data already in the
PersistentVolumes. Simply clean the directories mentioned in the
PV-yamls. Don't forget to check using "ls -la" as hidden files are
created by Spinnaker Pods.

h\) At this point, halyard job should start installing spinnaker. It
creates additional deployments. We can monitor the overall deployment by
checking the log (please replace with the correct pod-name):

kubectl log **oes-install-using-hal-XXXX** -n oes -f \# -f is for follow

\<Wait for the job to exit\>

**TIP:**

Following the log is a great way to figure out what halyard is doing
while bringing up and configuring Spinnaker

i\) Lets wait for some time for all the pods to be running. Note that
there are StatefulSets in the deployment and the pods are started in a
certain order.

Kubectl get po -n oes -w \# Wait for all pods in "0/1 Running" to change
to "1/1 Running" status

**TIP-SPIN-DECK:**

If spin-deck pod goes into CrashLoop, it will need to be given
root-permissions to run. Sample Yaml is in the git. Note that this may
have security implications.

kubectl edit deploy spin-deck \# and Change this line:

> securityContext: {}

to this:

> securityContext:
>
> runAsUser: 0

j\) Create spin-gate-np and make a note of the NodePort number
**\[Ideally this should be fixed in the GIT, this extra step is not
required\]**

> kubectl expose deploy spin-gate \--name spin-gate-np \--type NodePort
> \--port 8084 -n oes

or from git-file:

> kubectl apply -f spin-gate-np.yaml -n oes

k\) Get the Service port numbers, making a note of the NodePort numbers
for spin-deck-np and spin-gate-np:

Kubectl get svc -n oes

**Note spin-deck-np(30989) and spin-gate-np(32009) external ports**

![](.//media/image2.png){width="6.6930555555555555in"
height="1.7548611111111112in"}

l\) Copy kubeconfig file to Halyard pod. The example shows copying the
default "config" file. Ideally one should set-up a service account and
create a config-file that limits Spinnaker to a set of namespaces.

kubectl cp \~/.kube/config oes-spinnaker-halyard-0:/home/spinnaker/.kube
-n oes

m\) **Optional:** Now is also a good time to copy any other credentials
that spinnaker might need. For example, if you have created a
"token-file" for github access:

kubectl cp github-token oes-spinnaker-halyard-0:/home/spinnaker/.hal -n
oes

n\) Configure spinnaker by executing commands inside the halyard pod.
Open a shell inside the pod:

kubectl exec -it oes-spinnaker-halyard-0 -n oes \-- /bin/sh

\<wait for the \$ prompt\>

\#**Configure** Spinnaker for external access and set URL as per the
node-ports

echo \"host: 0.0.0.0\" \| tee \~/.hal/default/service-settings/gate.yml
\~/.hal/default/service-settings/deck.yml

hal config security ui edit \--override-base-url
http://10.168.3.11:**spin-deck-np**

hal config security api edit \--override-base-url
http://10.168.3.11:**spin-gate-np**

hal config features edit \--artifacts true \# This is generally a good
command to execute :-)

\#**OPTIONAL:** Configure Spinnaker for to deploy applications, replace
**OpsMx-k8s** with the identifier for this k8s cluster/account

hal config provider kubernetes account add **OpsMx-k8s**
\--provider-version v2 \--kubeconfig-file=/home/spinnaker/.kube/config
\--only-spinnaker-managed true

hal config provider kubernetes enable

\#**OPTIONAL:** Configure Spinnaker for github, replace
**OpsMx-k8s-Github** as appropriate

hal config artifact github account add **OpsMx-k8s-Github**
\--token-file /home/spinnaker/.hal/github-token

hal config artifact github enable

\#**OPTIONAL:** Configure Spinnaker for Jenkins. This is adequate to
trigger either one from the other. Replace **OpsMx-k8s-Jenkins** as
appropriate

BASEURL=http://\<host-name\>\[:8181\]/jenkins

USERNAME=username \#Spinnaker will use this username/passwd for
interaction with Jenkins

PASSWORD=passwd

hal config ci jenkins master add **OpsMx-k8s-Jenkins** \--address
\$BASEURL \--username \$USERNAME \--password \$PASSWORD

hal config ci jenkins enable

\#**OPTIONAL:** Configure Spinnaker for LDAP authentication using the
provided demo-LDAP server. Note that it is insecure and should not be
used in a production environment. Its best to replace the
ldap-**user-db-pattern** and ldap-**url** with the ldap your kids may be
playing with :-)

hal config security authn ldap edit \--user-dn-pattern=\"cn={0}\"
\--url=ldap://oes-openldap:389/dc=example,dc=org

hal config security authn ldap enable

\#**DON'T miss this one**

hal deploy apply \# Apply all the configurations above

\<wait for the command to complete\>

exit \# Exit the pod shell

**TIP:**

In the unlikely case that the spin-deck pod goes into crash-loop, please
apply the work-around mentioned above.

o\) Wait for all spinnaker pods to restart. The screen below indicates
that pods are still restarting:

![](.//media/image3.png){width="5.664583333333334in"
height="3.770138888888889in"}

Once all pods have restarted, the status should look like this:

![](.//media/image4.png){width="5.620138888888889in"
height="2.6131944444444444in"}

At this point PART-I (Simple and "it works", hopefully) should be
complete. Try opening Spinnaker in a browser:

http://10.168.3.11:spin-deck-np

\[You can login with <admin/OpsMx@123>, if demo - LDAP was used\]

\[Click on "Applications" and "oes" to see some data on the screen.\]

PART-II: Better-looking

Now that we got the application working in the most basic mode, lets
make it look a bit more "professional". There are multiple ways of doing
this. The best way is to configure a loadbalancer and have the two ports
(spin-deck-np and spin-gate-np) forward to the nodes in the k8s cluster.

Unforunately, I could not find a loadbalancer in my filing cabinet :-)
But I could find a spare desktop. So, here is an alternate solution
using HAProxy in a very simply configuration, as a starting point, and
then we make it a bit more interesting.

Here we will need another machine to host HAProxy and forward the
traffice to the nodes in the k8s cluster. We could, as a worst-case
scenario, use one of the k8s-nodes for hosting HAProxy (assuming that
port 80 is not already taken).

Lets get started with our machine designated as the "loadbalancer":

a\) Install Ubuntu 18.04 based on instructions **here.**

b\) Download and install HAProxy (version 1.9) based on instructions
**here**. Summary:

> sudo add-apt-repository -y ppa:vbernat/haproxy-1.9
>
> sudo apt-get update
>
> sudo apt-get install -y haproxy

c\) Configure HAproxy: Copy haproxy.cfg.sample (from git-repo) to
/etc/haproxy/haproxy.cfg and edit it as instructed below:

\...

\...

frontend deck

bind 10.168.3.20:80 \# change the IP-address of the machine haproxy is
running on

mode http

use\_backend deck-back if { path -i -m beg /ui/ }

use\_backend deck-back-2 if { path -i -m beg /ui }

use\_backend gate-back if { path -i -m beg /api/ }

use\_backend gate-back-2 if { path -i -m beg /api }

use\_backend gate-back if { path -i -m beg /login }

use\_backend gate-back if { path -i -m beg /auth/ }

use\_backend deck-back

backend deck-back

mode http

balance roundrobin

http-request set-path %\[path,regsub(\^/ui/,/)\]

server node1 10.168.3.11:30989 \# change the IP:Port to the
node-IP:spin-deck-np

server node1 10.168.3.10:30989 \# Multiple nodes can be added

backend deck-back-2

mode http

balance roundrobin

http-request set-path \"%\[path,regsub(\^/ui,/)\]\"

server node1 10.168.3.11:30989

server node1 10.168.3.10:30989

backend gate-back

mode http

balance roundrobin

http-request set-path %\[path,regsub(\^/api/,/)\]

server node1 10.168.3.11:32009 \# change the IP:Port to the
node-IP:spin-gate-np

server node1 10.168.3.10:32009

\#This is really not required, put-in here for completeness

backend gate-back-2

mode http

balance roundrobin

http-request set-path %\[path,regsub(\^/api,/)\]

server node1 10.168.3.11:32009

server node1 10.168.3.10:32009

d\) Configure Spinnaker to use the loadbalancer machine. Spinnaker's two
main components, "deck" (UI) and "gate" (backed-API) need not be on the
same machine. So, we need to tell them where to find each other.

kubectl exec -it oes-spinnaker-halyard-0 -n oes \-- /bin/sh

\<wait for the \$ prompt\>

*\# replace baremetalk8s.opsmx.com with the hostname.domain of
"loadbalancer machine"*

*\# Alternatively, use a name of your choice and put an entry in the
/etc/hosts file (example in git)*

hal config security ui edit \--override-base-url
http://baremetal*k8s*.opsmx.com/ui

hal config security api edit \--override-base-url
http://baremetal*k8s*.opsmx.com/api

hal deploy apply

exit \# Exit the pod shell

e\) Wait for all spinnaker pods to restart.

If required, add a DNS entry for IP address of our "loadbalancer"
machine. As an alternative, I have simply made an entry in the
/etc/hosts on "all" the machines (only 3 of them).

**And\...drum roll\...go to :**

[http://baremetal**k8s.opsmx.com/ui**](http://baremetalspin.opsmx.com/ui)

**You have a fully professional looking Spinnaker.**
