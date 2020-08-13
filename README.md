# OpsMx Enterprise Spinnaker

OpsMx Enterprise Spinnaker is an installation bundle that includes the open source Spinnaker and OpsMx extensions on top of it.

For more information, visit https://www.opsmx.com

## TL;DR;
Install OpsMx Enterprise Spinnaker
  ```console
  $ helm repo add opsmx https://helmcharts.opsmx.com/
  $ helm install <release-name> opsmx/oes
  ```
Install OpsMx Autopilot
  ```console
  $ helm repo add opsmx https://helmcharts.opsmx.com/
  $ helm install <release-name> opsmx/opsmx-autopilot
  ```
## Contents:
   1. Spinnaker + OES Setup Instructions
   2. Autopilot Setup Instructions

## 1. Spinnaker + OpsMx Enterprise Spinnaker Extensions (OES) Setup Instructions

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

### Installing the OpsMx Enterprise Spinnaker Extensions (OES) Spinnaker Chart

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
`installSpinnaker` | If true, install Spinnaker along with OES Extensions | `true`
`enableCentralLogging` | If true, install EFK stack on cluster | `false`
`createIngress` | If true, exposes Spinnaker deck & gate services over Ingress | `false`
`installOpenLdap` | If true, installs Open LDAP server | `true`
`k8sServiceType` | Service Type of oes-ui, oes-gate, spin-deck-ui, spin-gate | `LoadBalancer`
`imagePullSecret` | Name of the image pull secret to fetch oes docker images from private registry | `oes-repo`
`imageCredentials.registry` | The registry where OES docker images are available | `https://index.docker.io/v1/`
`imageCredentials.username` | Username of docker account to access docker registry | `dockerHubId`
`imageCredentials.password` | Password of docker account | `dockerHubPwd`
`imageCredentials.email` | Email associated with docker account | `abc@xyz.com`
`installRedis` | If true, OES will install its own Redis for caching | `false`
`redis.image.registry` | Registry to be used for docker images when installRedis is set to true | `docker.io`
`redis.image.repository` | Repository to be used for docker images when installRedis is set to true | `bitnami/redis`
`redis.image.tag` | Tag to be used for docker images when installRedis is set to true | `4.0.11-debian-9`
`redis.image.pullPolicy` | Redis image pull policy | `IfNotPresent`
`opsmxdb.enabled` | Set it to false if OpsMx DB is already installed on cluster | `true`
`opsmxdb.podManagementPolicy` | Rollout strategy for DB(statefulset) pods  | `OrderedReady`
`opsmxdb.securityContext.fsGroup` | FSGroup that owns the DB pod's volumes | `1000`
`opsmxdb.storageMountSize` | Storage to be allocated to OpsMx DB | `8Gi`
`oes.image.gate.registry` | Registry to be used for OES Gate docker images | `opsmx11`
`oes.image.gate.repository` | Repository to be used for OES Gate docker images | `oes-gate`
`oes.image.gate.tag` | Tag to be used for OES Gate docker images | `v0.202007101453`
`oes.image.gate.pullPolicy` | Image pull policy for OES Gate image | `IfNotPresent`
`oes.image.sapor.registry` | Registry to be used for OES SAPOR docker images | `opsmx11`
`oes.image.sapor.repository` | Repository to be used for OES SAPOR docker images | `sapor`
`oes.image.sapor.tag` | Tag to be used for OES SAPOR docker images | `v0.202007101007`
`oes.image.sapor.pullPolicy` | Image pull policy for OES SAPOR image | `IfNotPresent`
`oes.image.ui.registry` | Registry to be used for OES UI docker images | `opsmx11`
`oes.image.ui.repository` | Repository to be used for OES UI docker images | `oes-ui`
`oes.image.ui.tag` | Tag to be used for OES UI docker images | `v0.202007011835`
`oes.image.ui.pullPolicy` | Image pull policy for OES UI image | `IfNotPresent`
`oes.autoConfiguration.enabled` | Option enables OES to be configured automatically. Load Balancer IPs will be automatically replaced in the configuration files of oes-gate, oes-ui & sapor. Set it to false if OES is being installed on restricted evnironment. | `true`
`oes.autoConfiguration.initContainer.image` | Image to be used by Init container for auto configuration | `opsmx11/oes-init:v2`
`oes.autoConfiguration.initContainer.externalIpCheckDelay` | Expected delay in assigning load balancer IPs to oes-ui & oes-gate in secs | `180`
`oes.autoConfiguration.initContainer.spinnakerSetupMaxDelay` | Expected time in secs that it takes for Spinnaker to be up & running | `180`
`oes.config.db.dbUrl` | URL of DB for OES | `jdbc:postgresql://db-opsmx:5432/oesdb`
`oes.config.db.username` | Username to communicate with DB | `postgres`
`oes.config.db.username` | Password to communicate with DB | `networks123`
`oes.config.server.enabled` | Used by OES-GATE to reach SAPOR | `true`
`oes.config.server.baseUrl` | Used by OES-GATE to reach SAPOR | `http://sapor:8085`
`oes.config.spinnaker.oesGateURL` | Used by OES-UI to reach OES-GATE; Automatically configured if LoadBalancer is available | `http://OES_GATE_IP:8084/`
`oes.config.spinnaker.oesUIcors` | Regex of OES-UI IP/host for CORS; Automatically configured if LoadBalancer is available | `http://OES_GATE_IP:8084/`
`oes.config.spinnaker.spinGateURL` | No need to configure if Spinnaker is in the namespace as OES | `http://spin-gate:8084/`
`oes.config.spinnaker.spinExternalGateURL` | Used by OES-UI to display the link of Pipeline | `http://SPIN_GATE_LOADBALANCER_IP_PORT/`
`oes.config.spinnaker.spinuser` | Username to communicate with Spinnaker | `dummyuser`
`oes.config.spinnaker.spinpasswd` | Password to communicate with Spinnaker | `dummypwd`
`oes.config.spinnaker.adminLoginEnabled` | Set it to true if admin login is enabled in Spinnaker | `false`
`oes.config.spinnaker.authnEnabled` | Set it to true if authentication is enabled in Spinnaker | `false`
`oes.config.ldap.enabled` | Set it to true if LDAP is to be enabled for OES | `true`
`oes.config.ldap.url` | URL of LDAP server | `ldap://{{ .Release.Name }}-openldap:389`
`oes.config.ldap.userDnPattern` | DN Pattern for Open LDAP | `cn={0}`
`oes.config.ldap.basedn` | Base DN value | `dc=example,dc=org`
`oes.config.ldap.pattern` | Base DN filter pattern | `(&(cn=USERNAME))`
`oes.config.caCerts.override` | If default java certs are to be overwritten, create custom config map 'oes-sapor-cacerts.yaml' under templates and set this option to true | `false`
`openldap.adminPassword` | Password to be set for admin user of LDAP | `admin`
`openldap.omitClusterIP` | Set to true to omit ClusterIP for openldap service | `true`
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

##### Connecting to OpsMx Enterprise Spinnaker Extensions(OES)

  Once the service is up and running, find the service ip address

  	kubectl get svc oes-ui [--namespace mynamespace]

  Example output would be:

    NAME 	     TYPE             CLUSTER-IP   EXTERNAL-IP     PORT(S)          AGE
    oes          LoadBalancer     10.0.33.110  52.149.54.222   80:30860/TCP     20h

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

## 2. Autopilot Setup Instructions

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

### Installing the OpsMx Autopilot Chart

- Add opsmx helm repo to your local machine

   ```console
   $ helm repo add opsmx https://helmcharts.opsmx.com/
   ```

- Docker registry credentials is setup as a secret in Kubernetes. Before you install Autopilot, please send an email to support@opsmx.com requesting access to the Autopilot images with your Dockerhub id. You can proceed with installation once your Dockerhub id has been granted access.

  To be able to fetch Autopilot docker images, username and password shall be set in values.yaml or use --set imageCredentials.username=<username> --set imageCredentials.password=<password> while running helm install.

- Your Kubernetes cluster supports persistent volumes and loadbalancer service type.

- Helm v3 expects the namespace to be present before helm install command is run. If it does not exists,

  ```console
  $ kubectl create namespace mynamespace
  ```

- To install the chart with the release name `my-release`:

  Helm v2.x
  ```console
  $ helm install --name my-release opsmx/opsmx-autopilot [--namespace mynamespace]
  ```
	Helm v3.x
  ```console
  $ helm install my-release opsmx/opsmx-autopilot [--namespace mynamespace]
  ```

The command deploys Autopilot on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

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

The following table lists the configurable parameters of the Autopilot chart and their default values.

Parameter | Description | Default
--------- | ----------- | -------
`imagePullSecret` | Name of the image pull secret to fetch autopilot docker images from private registry | `autopilot-repo`
`imageCredentials.registry` | The registry where Autopilot docker images are available | `https://index.docker.io/v1/`
`imageCredentials.username` | Username of docker account to access docker registry | `dockerHubId`
`imageCredentials.password` | Password of docker account | `dockerHubPwd`
`imageCredentials.email` | Email associated with docker account | `abc@xyz.com`
`autopilot.image.registry` | Registry to be used for Autopilot docker images | `opsmxdev`
`autopilot.image.repository` | Repository to be used for Autopilot docker images | `ubi8-autopilot`
`autopilot.image.tag` | Tag to be used for Autopilot docker images | `v2.9.10-202006181240`
`autopilot.image.pullPolicy` | Image pull policy for Autopilot image | `IfNotPresent`
`autopilot.service.type` | Service type over which autopilot is to be exposed | `LoadBalancer`
`autopilot.config.pythonAlgorithm` | Algorithm for Data Science | `spell`
`autopilot.config.buildAnalysis.enabled` | Set it to false to disable build analysis | `false`
`autopilot.config.dataSource.url` | URL of DB for Autopilot | `jdbc:postgresql://db-opsmx:5432/opsmx`
`autopilot.config.dataSource.username` | Username to communicate with DB | `postgres`
`autopilot.config.dataSource.username` | Password to communicate with DB | `networks123`
`autopilot.config.spinnaker.loginAdminEnabled` | Set it to true if admin login is enabled in Spinnaker | `false`
`autopilot.config.spinnaker.spinGateUrl` | Spinnaker Gate URL to trigger Canary Analysis | `http://spin-gate:8084`
`autopilot.config.appConfigJS.autopilotServerUrl` | URL of Autopilot to be used by UI to reach the backend. app.config.js file in configuration appends http:// to the provided URL | `autopilot:8090`
`autopilot.config.spinnaker.spinUsername` | Username to communicate with Spinnaker | `dummyusername`
`autopilot.config.spinnaker.spinPassword` | Password to communicate with Spinnaker | `dummypassword`
`autopilot.config.ldap.authEnabled` | Set it to true if LDAP is to be enabled for Autopilot | `true`
`autopilot.config.ldap.url` | URL of LDAP server | `ldap://oes-openldap:389`
`autopilot.config.ldap.userDnPattern` | DN Pattern for Open LDAP | `cn={0}`
`autopilot.config.ldap.basedn` | Base DN value | `cn=Users,dc=local,dc=opsmx,dc=com`
`autopilot.config.ldap.pattern` | Base DN filter pattern | `(&(objectclass=person)(cn=USERNAME))`
`autopilot.config.ssl.enabled` | Set it to true to enable SSL | `false`
`autopilot.config.ssl.keyStore` | SSL Key Store | `keystore.p12`
`autopilot.config.ssl.keyStorePassword` | SSL Key Store Password | `dummypwd`
`autopilot.config.ssl.keyStoreType` | SSL Key Store Type | `PKCS12`
`autopilot.config.ssl.keyAlias` | SSL key alias | `tomcat`
`opsmxdb.enabled` | Set it to false if OpsMx DB is already installed on cluster | `true`
`opsmxdb.podManagementPolicy` | Rollout strategy for DB(statefulset) pods  | `OrderedReady`
`opsmxdb.securityContext.fsGroup` | FSGroup that owns the DB pod's volumes | `1000`
`opsmxdb.storageMountSize` | Storage to be allocated to OpsMx DB | `8Gi`


> **Tip**: Refer to values.yaml for detailed comments


Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

  ```console
  $ helm install my-release opsmx/opsmx-autopilot --set imageCredentials.username=<username> --set imageCredentials.password=<password> [--namespace mynamespace]
  ```

Alternatively, a YAML file that specifies the values for the above parameters can be provided while installing the chart. For example, Autopilot values.yaml can be first downloaded using below command and then customized.

wget https://raw.githubusercontent.com/opsmx/enterprise-spinnaker/oes3.0/charts/opsmx-autopilot/values.yaml

Helm v2.x
  ```console
  $ helm install opsmx/opsmx-autopilot --name my-release -f values.yaml
  ```
Helm v3.x
  ```console
  $ helm install my-release opsmx/opsmx-autopilot -f values.yaml
  ```

### Connecting to Autopilot

  Once the service is up and running, find the service ip address

  		kubectl get svc autopilot [--namespace mynamespace]

  Example output would be:

      NAME         TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)                                        AGE
      autopilot    LoadBalancer   10.0.4.246   34.66.226.138   8090:32097/TCP,8161:32527/TCP,9090:31265/TCP   9m11s

  Now, UI can be accessed via EXTERNAL-IP address, go to http://<EXTERNAL-IP>:8161/
