**Installing Open Enterprise Spinnaker (OES) on Single Node kubernetes**

Install a Spinnaker instance with-in an hour using an opinionated
developer install. Please note that this installation is not suitable
for production use.

Before going through the installation steps, its a great idea to go
through the following:

https://blog.opsmx.com/open-enterprise-spinnaker/ and

https://github.com/OpsMx/enterprise-spinnaker/tree/master/charts/oes

What you need: A laptop or desktop running Ubuntu 18.04 with i5(8 core),
32GB Memory and 500GB SSD. Access to the monitor (or display) is
required.

Before you install OES, **please send an email to
[[spinnaker-poc\@opsmx.io]{.underline}](mailto:spinnaker-poc@opsmx.io)**
requesting access to the OES images. We would require your dockerhub id
to grant you access. If you do not already have a dockerhub id, you can
get one at [https://hub.docker.com](https://hub.docker.com/) .

**Software Setup**

Open a terminal (ctrl+alt+T), create a temporary directory and CD into
it

1\) Install virtualbox 5.2 from
[[here]{.underline}](https://qiita.com/shaching/items/4fcc95f20cff2450aa8f).

2\) Install Vagrant version 2.2.4 from
[[here]{.underline}](https://linuxize.com/post/how-to-install-vagrant-on-ubuntu-18-04).

3\) Install disksize plugin using this command: vagrant plugin install
vagrant-disksize

**Spinnaker Installation Procedure**

A\) git clone <https://github.com/ksrinimba/enterprise-spinnaker.git>

B\) cd enterprise-spinnaker/opinionated

C\) Edit inst\_oes.sh and update "docker-username" and "docker-password"
for the OES images

D\) vagrant up \# Create VMs, install k8s & Spinnaker, takes about 30
minutes)

E\) Access Spinnaker URL (printed above) on from the host machine (Login
with <admin/OpsMx@123>)

**TIPS to handle anyerrors:**

a\) If spin-deck pod goes into CrashLoop, it will need to be given
root-permissions to run. Sample spin-deck.yaml is in the git. Note that
this may have security implications.

kubectl edit deploy spin-deck \# and Change this line:

> securityContext: {}

to this:

> securityContext:
>
> runAsUser: 0

b\) The application URL is
[[http://10.168.3.10]{.underline}](http://10.168.3.10/):{DECK NodePort}
can be obtained with this command on the master node:

kubectl get svc spin-deck-ui -n oes -o
jsonpath=\'{\"[http://10.168.3.10](http://10.168.3.10/)[:\"}{\...nodePort}{\"\\n\"}\']()
