<p align="center">
	<img src="img/opsmx.png" width="20%" align="center" alt="OpsMx">
</p>

# OpsMx Enterprise for Spinnaker

OpsMx Enterprise for Spinnaker is an installation bundle that includes the open source Spinnaker and OpsMx extensions on top of it.

For more information, visit https://www.opsmx.com

## TL;DR;
Install OpsMx Enterprise for Spinnaker
  ```console
  $ helm repo add opsmx https://helmcharts.opsmx.com/
  $ helm install <release-name> opsmx/oes --set imageCredentials.username=<dockerID> --set imageCredentials.password=<dockerPassword>
  ```

## Spinnaker + OpsMx Enterprise for Spinnaker Extensions (OES) Setup Instructions

### Prerequisites

- Kubernetes cluster 1.19 or later with at least 6 cores and 20 GB memory
- Helm 3 is setup on client system
  ```console
  $ helm version
  ```
  If helm is not setup, follow <https://helm.sh/docs/intro/install/> to install helm.

### Installing the OpsMx Enterprise for Spinnaker Extensions (OES) Spinnaker Chart

- Add opsmx helm repo to your local machine

   ```console
   $ helm repo add opsmx https://helmcharts.opsmx.com/
   ```

  Note: If opsmx helm repo is already added, do a repo update before installing the chart

   ```console
   $ helm repo update
   ```

- Your Kubernetes cluster shall support persistent volumes

- It is assumed that an nginx ingress controller is installed on the cluster, by default ingress resources are created for oes-ui, oes-gate, spin-deck and spin-gate services. Customize the hosts for OES using the options in the values.yaml under global.oesUI, oesGate, spinDeck, spinGate. If any other ingress controller is installed, set createIngress flag to false and configure your ingress.

- To enable mutual TLS for Spinnaker Services and SSL features provided by Spinnaker Life Cycle Management (LCM), it is required to install nginx ingress from kubernetes community and cert-manager before installing OES. Please refer the table below for options to be enabled for LCM
  Instructions to install nginx ingress
  https://kubernetes.github.io/ingress-nginx/deploy/

  Instructions to install cert-manager
  https://cert-manager.io/docs/installation/kubernetes/

- Helm v3 expects the namespace to be present before helm install command is run. If it does not exists,

  ```console
  $ kubectl create namespace mynamespace
  ```

- To install the chart with the release name `my-release`:

	Helm v3.x
  ```console
  $ helm install my-release opsmx/oes [--namespace mynamespace]
  ```

The command deploys OES on the Kubernetes cluster in the default configuration. The [configuration](#configuration) section lists the parameters that can be configured during installation.

> **Tip**: List all releases using `helm list`

### Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

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
`rbac.create` | Enable or disable rbac | `true`
`installSpinnaker` | If true, install Spinnaker along with OES Extensions | `true`
`installationMode` | The installation mode. Available installation modes are **OES-AP** (for OES that includes Autopilot) and **None**(Skip OES installation) and **EASY** installation on minikube or microk8s| `OES-AP`
`global.certManager.installed` | Disable this flag if cert-manager is not installed, when set to true issuer and TLS certs for ingress are automatically created | `true`
`global.createIngress` | If true, exposes OES ui & gate services over Ingress | `false`
`global.spinDeck.protocol` | Change this to https if TLS is enabled for ingress endpoint | `http`
`global.spinDeck.host` | Host using which spinnaker deck needs to be accessed | `spinnaker.example.org`
`global.spinDeck.ingress.annotations` | Annotations for deck ingress resource | ``
`global.spinDeck.ingress.tls.secretName` | Change this value if your own certificate is put into a specific secret | `deck-authtls` 
`global.spinGate.protocol` | Change this to https if TLS is enabled for ingress endpoint | `http`
`global.spinGate.host` | Host using which spinnaker gate needs to be accessed | `gate.spinnaker.example.org`
`global.spinGate.ingress.annotations` | Annotations for spinnaker gate ingress resource | ``
`global.spinGate.ingress.tls.secretName` | Change this value if your own certificate is put into a specific secret | `gate-authtls`
`global.oesUI.protocol` | Change this to https if TLS is enabled for ingress endpoint | `http`
`global.oesUI.host` | Host using which UI needs to be accessed | `oes.domain.com`
`global.oesGate.protocol` | Change this to https if TLS is enabled for ingress endpoint | `http`
`global.oesGate.host` | Host using which Gate needs to be accessed | `oes-api.domain.com`
`global.enableCentralMonitoring` | Enable monitoring for Spinnaker | `false`
`k8sServiceType` | Service Type of oes-ui, oes-gate, spin-deck-ui, spin-gate | `LoadBalancer`
`installRedis` | If true, OES will install its own Redis for caching. This option is mutually exclusive with installSpinnaker | `false`
`redis.url` | Set custom URL if installRedis is set to false | `redis://{{ .Release.Name }}-redis-master:6379`
`db.enabled` | Set it to false if OpsMx DB is already installed on cluster or if any external database is to be used.| `true`
`db.url` | URL of the external DB if not using OpsMx DB.| `jdbc:postgresql://oes-db:5432/opsmx`
`db.storageMountSize` | Storage to be allocated to OpsMx DB | `8Gi`
`autopilot.config.buildAnalysis.enabled` | Set it to false to disable build analysis | `false`
`autopilot.config.ssl.enabled` | Set it to true to enable SSL | `false`
`autopilot.config.ssl.keystore` | SSL keystore value | `keystore.p12`
`autopilot.config.ssl.keyStorePassword` | SSL keystore password | `dummypwd`
`autopilot.config.ssl.keyStoreType` | SSL keystore type | `PKCS12`
`autopilot.config.ssl.keyAlias` | SSL key alias | `tomcat`
`dashboard.spinnakerLink` | Specify if dashboard needs to be configured with a different spinnaker | `{{ .Values.spinnaker.ingress.protocol }}://{{ .Values.spinnaker.ingress.host }}`
`gate.config.global.oesUIcors` | Regex of OES-UI URL to prevent cross origin attacks | `^https?://(?:localhost|OES_UI_LOADBALANCER_IP|opsmx.com)(?::[1-9]\d*)?/?`
`gate.config.fileBasedAuthentication` | Set it to true to disable LDAP authentication and enable file based authentication | `false`
`gate.config.saml` | SAML configuration for oes gate authn and authz | ``
`gate.config.saml.jksSecretName` | Set this value to use an existing secret in which saml jks exists | `oes-saml-jks`
`gate.config.saml.metadataSecretName` | Set this value to use an existing secret in which saml metadata exists | `metadata-xml`
`gate.config.oauth2` | OAuth2 configuration for oes gate authn and authz | ``
`platform.config.adminGroups` | Admin groups available | `admin, Administrators`
`platform.config.userSource` | Source of Users for authorization | `ldap`
`platform.config.supportedFeatures` | List of featues to be supported by OES | `[deployment_verification, sapor, visibility]`
`sapor.config.spinnaker.authnEnabled` | Set it to true if authentication is enabled in Spinnaker | `false`
`sapor.config.spinnaker.spinGateURL` | URL of Spinnaker Gate | `http://spin-gate.oes-spin:8084`
`sapor.config.spinnaker.spinExternalGateURL` | By default this is set to spinnaker installed in the same namespace; change this when different spinnaker needs to be configured with sapor | `{{ .Values.spinnaker.ingress.protocol }}://{{ .Values.spinnaker.ingress.host }}`
`sapor.config.spinnaker.ldap.ldapEnabled` | Is LDAP authn enabled for spinnaker | `true`
`sapor.config.spinnaker.ldap.ldapUsername` | Spinnaker username | `admin`
`sapor.config.spinnaker.ldap.ldapPassword` | Spinnaker password | `opsmxadmin123`
`sapor.config.spinnaker.x509.enabled` |  Is x509 cert authn enabled for spinnaker | `false`
`sapor.config.spinnaker.x509.client.password` |  Password of x509 client certificate | `changeit`
`sapor.config.kubernetes.agent.enabled` | Option to enable oes kubernetes agent | `true`
`sapor.config.caCerts.override` | If default java certs are to be overwritten, create custom config map 'oes-sapor-cacerts.yaml' under templates and set this option to true | `false`
`ui.config.setApplicationRefreshInterval` | Interval at which UI refreshes application dashboard | `16000`
`visibility.config.configuredConnectors` | Integrations options | `JIRA,GIT,AUTOPILOT,SONARQUBE,JENKINS,AQUAWAVE`
`visibility.config.logLevel` | Default Log Level | `ERROR`
`global.autoConfiguration.enabled` | Option enables OES to be configured automatically. Load Balancer IPs will be automatically replaced in the configuration files of oes-gate, oes-ui & sapor. Set it to false if OES is being installed on restricted environment. | `true`
`global.autoConfiguration.initContainer.externalIpCheckDelay` | Expected delay in assigning load balancer IPs to oes-ui & oes-gate in secs | `180`
`opa.enabled` | Enable OPA with OES | `true`
`installOpenLdap` | If true, installs Open LDAP server | `false`
`openldap.adminPassword` | Password to be set for admin user of LDAP | `opsmxadmin123`
`ldap.enabled` | Set it to true if LDAP is to be enabled for OES | `true`
`ldap.url` | URL of LDAP server | `ldap://{{ .Release.Name }}-openldap:389`
`spinnaker.enableHA` | Enable HA for orca & echo | `true`
`spinnaker.gitopsHalyard.enabled` | Enable gitops style halyard & account config | `false`
`spinnaker.gitopsHalyard.mTLS.enabled` | Enable mTLS for Spinnaker Services and SSL for Deck and Gate | `false`
`spinnaker.gitopsHalyard.mTLS.deckIngressHost` | Ingress host for deck | `spindeck.{{ .Release.Name }}.domain.com`
`spinnaker.gitopsHalyard.mTLS.gateIngressHost` | Ingress host for gate | `spingate.{{ .Release.Name }}.domain.com`
`spinnaker.gitopsHalyard.repo-type` | Repo type; git, s3, vault | `git`
`spinnaker.gitopsHalyard.secretName` | Secret in which git credentials shall be specified, sample secret found under templates/secrets/ | `opsmx-gitops-auth`
`spinnaker.gitopsHalyard.spinnakerLBCheckDelay` | Timeout while fetching LB IPs of spin-deck and spin-gate to configure in hal config in seconds | `180`
`spinnaker.gitopsHalyard.gatex509.enabled` | Flag to enable x509 authentication for gate and use it for webhooks | `false`
`spinnaker.gitopsHalyard.gatex509.host` | Separate host for using x509 authentication | `spingate-x509.domain.com`
`spinnaker.gitopsHalyard.pipelinePromotion.enabled` | To Enable pipeline promotion from one env to another | `false`
`spinnaker.spinCli` | Authn credentials to enable spin-cli container to automatically populate sample pipelines while spinnaker is starting up | ``

> **Tip**: Refer to values.yaml for detailed comments

> **Tip**: Refer to Spinnaker helm chart & EFK helm chart for their configuration details.

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

  ```console
  $ helm install my-release opsmx/oes --set installSpinnaker=false --set installRedis=true --set imageCredentials.username=username \
  --set imageCredentials.password=password [--namespace mynamespace]
  ```

Alternatively, a YAML file that specifies the values for the above parameters can be provided while installing the chart. For example, OES values.yaml can be first downloaded using below command and then customized.

wget https://raw.githubusercontent.com/opsmx/enterprise-spinnaker/master/charts/oes/values.yaml

Helm v3.x
  ```console
  $ helm install my-release opsmx/oes -f values.yaml
  ```

### Connecting to Spinnaker and OpsMx Enterprise Extensions

#### Connecting to Spinnaker

  Once the service is up and running, find the service ip address

  	kubectl get svc spin-deck-np [--namespace mynamespace]

  Example output would be:

      NAME           TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
      spin-deck-np   LoadBalancer   10.0.139.222   40.78.4.201   9000:31030/TCP   8m9s

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
