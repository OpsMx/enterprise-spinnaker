# OpsMx Enterprise for Spinnaker

OpsMx Enterprise for Spinnaker is an installation bundle that includes the open source Spinnaker and OpsMx extensions on top of it.

For more information, visit https://www.opsmx.com

## TL;DR;
Install OpsMx Enterprise for Spinnaker
  ```console
  $ helm repo add opsmx https://helmcharts.opsmx.com/
  $ helm install <release-name> opsmx/oes
  ```

## Spinnaker + OpsMx Enterprise for Spinnaker Extensions (OES) Setup Instructions

### Prerequisites

- Kubernetes cluster 1.13 or later with at least 6 cores and 20 GB memory
- Helm is setup and initialized in your Kubernetes cluster
  ```console
  $ helm version
  ```
  If helm is not setup, follow <https://helm.sh/docs/using_helm/#install-helm> to install helm.

  If you are using helm v2.x, you need to initialize the Kubernetes to work with helm. If using helm v2.x, the helm version command should return both the client and server versions. If it does not return both client and server versions, you can follow these three simple steps to initialize helm v2.x in the kubernetes cluster:

  ```console
  $ kubectl create serviceaccount -n kube-system tiller
  $ kubectl create clusterrolebinding tiller-binding --clusterrole=cluster-admin --serviceaccount kube-system:tiller
  $ helm init --service-account tiller --wait
  ```

### Installing the OpsMx Enterprise for Spinnaker Extensions (OES) Spinnaker Chart

- Add opsmx helm repo to your local machine

   ```console
   $ helm repo add opsmx https://helmcharts.opsmx.com/
   ```

- Docker registry credentials is setup as a secret in Kubernetes. Before you install Autopilot, please send an email to support@opsmx.com requesting access to the Autopilot images with your Dockerhub id. You can proceed with installation once your Dockerhub id has been granted access.

  To be able to fetch OES docker images, username and password shall be set in values.yaml or use --set imageCredentials.username=<username> --set imageCredentials.password=<password> while running helm install.

- Your Kubernetes cluster supports persistent volumes and loadbalancer service type.

- Helm v3 expects the namespace to be present before helm install command is run. If it does not exists,

  ```console
  $ kubectl create namespace mynamespace
  ```

- To install the chart with the release name `my-release`:

  Helm v2.x
  ```console
  $ helm install --name my-release opsmx/oes [--namespace mynamespace]
  ```
	Helm v3.x
  ```console
  $ helm install my-release opsmx/oes [--namespace mynamespace]
  ```

The command deploys OES on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

> **Tip**: List all releases using `helm list`

### Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

Helm v2.x
  ```console
  $ helm delete my-release [--namespace mynamespace]
  ```

Helm v3.x
  ```console
  $ helm uninstall my-release [--namespace mynamespace]
  ```

The command removes all the Kubernetes components associated with the chart and deletes the release.

### Configuration

The following table lists the configurable parameters of the OES chart and their default values.

Parameter | Description | Default
--------- | ----------- | -------
`imagePullSecret` | Name of the image pull secret to fetch oes docker images from private registry | `opsmxdev-secret`
`imageCredentials.registry` | The registry where OES docker images are available | `https://index.docker.io/v1/`
`imageCredentials.username` | Username of docker account to access docker registry | `dockerID`
`imageCredentials.password` | Password of docker account | `dockerPassword`
`imageCredentials.email` | Email associated with docker account | `info@opsmx.com`
`rbac.create` | Enable or disable rbac | `true`
`installSpinnaker` | If true, install Spinnaker along with OES Extensions | `false`
`installationMode` | The installation mode. Available installation modes are **OES-AP** (both OES 3.0 and Autopilot), **OES** (Only OES 3.0) and **AP** (Only Autopilot) | `OES-AP`
`createIngress` | If true, exposes Spinnaker deck & gate services over Ingress | `false`
`k8sServiceType` | Service Type of oes-ui, oes-gate, spin-deck-ui, spin-gate | `LoadBalancer`
`installOpenLdap` | If true, installs Open LDAP server | `false`
`openldap.adminPassword` | Password to be set for admin user of LDAP | `admin`
`openldap.omitClusterIP` | Set to true to omit ClusterIP for openldap service | `true`
`ldap.enabled` | Set it to true if LDAP is to be enabled for OES | `true`
`ldap.url` | URL of LDAP server | `ldap://{{ .Release.Name }}-openldap:389/dc=example,dc=org`
`ldap.userDnPattern` | DN Pattern for Open LDAP | `cn={0}`
`ldap.basedn` | Base DN value | `dc=example,dc=org`
`ldap.adminDn` | Admin DN value | `cn=admin,dc=example,dc=com`
`ldap.adminPassword` | Admin password | `adminroot123`
`ldap.userDisplayName` | Display name of the user | `displayName`
`ldap.pattern` | Base DN filter pattern | `(&(cn=USERNAME))`
`ldap.GroupIdentity` | User group identity | `memberOf`
`ldap.userIdentity` | User identity | `cn`
`installRedis` | If false, OES will uninstall its own Redis for caching | `true`
`redis.image.registry` | Registry to be used for docker images when installRedis is set to true | `docker.io`
`redis.image.repository` | Repository to be used for docker images when installRedis is set to true | `redis`
`redis.image.tag` | Tag to be used for docker images when installRedis is set to true | `true`
`redis.image.pullPolicy` | Redis image pull policy | `IfNotPresent`
`redis.image.url` | Set custom URL if installRedis is set to false | `redis://{{ .Release.Name }}-redis-master:6379`
`db.enabled` | Set it to false if OpsMx DB is already installed on cluster or if any external database is to be used.| `true`
`db.url` | URL of the external DB if not using OpsMx DB.| `jdbc:postgresql://oes-db:5432/opsmx`
`db.username` | Username of the DB.| `postgres`
`db.password` | Password of the DB.| `networks123`
`db.image.registry` | Registry to be used for docker images.| `opsmxdev`
`db.image.repository` | Repository to be used for docker images.| `ubi8-autopilot-db`
`db.image.tag` | Tag to be used for docker images.| `v1.5`
`db.image.pullPolicy` | DB image pull policy.| `IfNotPresent`
`db.podManagementPolicy` | Rollout strategy for DB(statefulset) pods  | `OrderedReady`
`db.securityContext.fsGroup` | FSGroup that owns the DB pod's volumes | `1000`
`db.storageMountSize` | Storage to be allocated to OpsMx DB | `8Gi`
`autopilot.image.registry` | Registry to be used for Autopilot docker images | `opsmx11`
`autopilot.image.repository` | Repository to be used for Autopilot docker images | `autopilot`
`autopilot.image.tag` | Tag to be used for Autopilot docker images | `master-202008210408`
`autopilot.image.pullPolicy` | Image pull policy for Autopilot image | `IfNotPresent`
`autopilot.config.buildAnalysis.enabled` | Set it to false to disable build analysis | `false`
`autopilot.config.ssl.enabled` | Set it to true to enable SSL | `false`
`autopilot.config.ssl.keystore` | SSL keystore value | `keystore.p12`
`autopilot.config.ssl.keyStorePassword` | SSL keystore password | `dummypwd`
`autopilot.config.ssl.keyStoreType` | SSL keystore type | `PKCS12`
`autopilot.config.ssl.keyAlias` | SSL key alias | `tomcat`
`dashboard.image.registry` | Registry to be used for dashboard images | `opsmx11`
`dashboard.image.registry` | Registry to be used for dashboard images | `opsmx11`
`dashboard.image.repository` | Repository to be used for dashboard images | `dashboard-service`
`dashboard.image.tag` | Tag to be used for dashboard images | `master-202009100512`
`dashboard.image.pullPolicy` | Image pull policy for dashboard image | `IfNotPresent`
`gate.image.registry` | Registry to be used for OES Gate docker images | `opsmx11`
`gate.image.repository` | Repository to be used for OES Gate docker images | `oes-gate`
`gate.image.tag` | Tag to be used for OES Gate docker images | `v0.202009031444`
`gate.image.pullPolicy` | Image pull policy for OES Gate image | `IfNotPresent`
`gate.config.oesUIcors` | Regex of OES-UI URL to prevent cross origin attacks | `^https?://(?:localhost|OES_UI_LOADBALANCER_IP|opsmx.com)(?::[1-9]\d*)?/?`
`gate.config.fileBasedAuthentication` | Set it to true to disable LDAP authentication and enable file based authentication | `false`
`platform.image.registry` | Registry to be used for platform docker images | `opsmx11`
`platform.image.repository` | Repository to be used for platform docker images | `platform-service`
`platform.image.tag` | Tag to be used for platform docker images | `master-202009100512`
`platform.image.pullPolicy` | Image pull policy for OES platform | `IfNotPresent`
`platform.config.adminGroups` | Admin groups available | `admin, Administrators`
`platform.config.userSource` | Source of Users for authorization | `ldap`
`sapor.image.registry` | Registry to be used for OES SAPOR docker images | `opsmx11`
`sapor.image.repository` | Repository to be used for OES SAPOR docker images | `sapor`
`sapor.image.tag` | Tag to be used for OES SAPOR docker images | `v0.202009111046`
`sapor.image.pullPolicy` | Image pull policy for OES SAPOR image | `IfNotPresent`
`sapor.config.spinnaker.authnEnabled` | Set it to true if authentication is enabled in Spinnaker | `false`
`sapor.config.spinnaker.spinGateURL` | URL of Spinnaker Gate | `http://spin-gate.oes-spin:8084`
`sapor.config.spinnaker.spinExternalGateURL` | Set the external IP address of spin-gate, this is used to redirect to the spinnaker pipelines from OES-UI | `http://spin-gate.oes-spin:8084`
`sapor.config.spinnaker.spinuser` | Spinnaker username | `admin`
`sapor.config.spinnaker.spinpasswd` | Spinnaker username | `opsmx@123`
`sapor.config.spinnaker.spinAdminLoginEnabled` | Enable to override spinnaker user credentials as an admin user | `false`
`sapor.config.spinnaker.spinAdminUsername` | Spinnaker admin username | `admin`
`sapor.config.spinnaker.spinAdminPassword` | Spinnaker admin password | `admin`
`sapor.config.caCerts.override` | If default java certs are to be overwritten, create custom config map 'oes-sapor-cacerts.yaml' under templates and set this option to true | `false`
`ui.image.registry` | Registry to be used for OES UI docker images | `opsmx11`
`ui.image.repository` | Repository to be used for OES UI docker images | `oes-ui`
`ui.image.tag` | Tag to be used for OES UI docker images | `v0.202009101444`
`ui.image.pullPolicy` | Image pull policy for OES UI image | `IfNotPresent`
`ui.config.oesGateURL` | Endpoint of oes-gate to be used by oes-ui | `http://OES_GATE_IP:8084/`
`ui.config.setApplicationRefreshInterval` | Interval at which UI refreshes application dashboard | `16000`
`autoConfiguration.enabled` | Option enables OES to be configured automatically. Load Balancer IPs will be automatically replaced in the configuration files of oes-gate, oes-ui & sapor. Set it to false if OES is being installed on restricted environment. | `true`
`autoConfiguration.initContainer.image` | Image to be used by Init container for auto configuration | `opsmx11/oes-init:v3`
`autoConfiguration.initContainer.externalIpCheckDelay` | Expected delay in assigning load balancer IPs to oes-ui & oes-gate in secs | `120`
`opa.enabled` | Enable OPA with OES | `true`
`opa.image.repository` | OPA image repository | `openpolicyagent/opa`
`opa.image.tag` | Tag to pull OPA image | `latest`
`opa.image.pullPolicy` | Image pull policy | `IfNotPresent`

> **Tip**: Refer to values.yaml for detailed comments

> **Tip**: Refer to Spinnaker helm chart & EFK helm chart for their configuration details.

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

  ```console
  $ helm install my-release opsmx/oes --set installSpinnaker=false --set installRedis=true --set imageCredentials.username=username \
  --set imageCredentials.password=password [--namespace mynamespace]
  ```

Alternatively, a YAML file that specifies the values for the above parameters can be provided while installing the chart. For example, OES values.yaml can be first downloaded using below command and then customized.

wget https://raw.githubusercontent.com/opsmx/enterprise-spinnaker/oes3.0/charts/oes/values.yaml

Helm v2.x
  ```console
  $ helm install opsmx/oes --name my-release -f values.yaml
  ```
Helm v3.x
  ```console
  $ helm install my-release opsmx/oes -f values.yaml
  ```

### Connecting to Spinnaker and OpsMx Enterprise Enterprise Extensions

#### Connecting to Spinnaker

  Once the service is up and running, find the service ip address

  	kubectl get svc spin-deck-ui [--namespace mynamespace]

  Example output would be:

      NAME           TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
      spin-deck-ui   LoadBalancer   10.0.139.222   40.78.4.201   9000:31030/TCP   8m9s

  Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:9000/

##### Connecting to OpsMx Enterprise for Spinnaker Extensions(OES)

  Once the service is up and running, find the service ip address

  	kubectl get svc oes-ui [--namespace mynamespace]

  Example output would be:

    NAME        TYPE              CLUSTER-IP      EXTERNAL-IP     PORT(S)         AGE
    oes-ui      LoadBalancer      10.0.33.110     52.149.54.222   80:30860/TCP    20m

  Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:80/

  You can login with dummysuer/dummypwd


##### Enabling centralized logging
  Spinnaker consists of multiple microservices and you need to connect to each microservice to see what is going on. We have enabled elasticsearch, fluentbit and kibana to provide a centralized logging solution for Spinnaker. To enable it, you need to install with the flag

  	    --set enableCentralLogging=true

  Note, that out-of-the-box configuration of the service requires addition 2G of memory and 1 core.
  To get the hostname for Kibana, run

  	    kubectl get svc [--namespace mynamespace]

  and find the service with Kibana in the name. Example output would be:

      NAME               TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)      AGE
      somename-kibana    LoadBalancer   10.0.4.246   34.66.226.138   5601:32097   9m43s

  Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:5601

  In Kibana, go to Discover -> Open -> Spinnaker Logs to see logs from Spinnaker pods.
