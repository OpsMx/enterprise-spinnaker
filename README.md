# OpsMx Enterprise for Spinnaker

OpsMx Enterprise for Spinnaker is an installation bundle that includes the open source Spinnaker and OpsMx extensions on top of it.

For more information, visit https://www.opsmx.com

## TL;DR;
Install OpsMx Enterprise for Spinnaker, quick steps:
  ```console
  $ helm repo add opsmx https://helmcharts.opsmx.com/
  $ helm install <release-name> opsmx/oes --set imageCredentials.username=<dockerID> --set imageCredentials.password=<dockerPassword>
  ```

Follow details in the next section for options available and step by step instructions.

## Contents:
   1. Custom Spinnaker + OES Setup Instructions
   2. Stable/Open Source Spinnaker Installation Instructions

## 1. Custom Spinnaker + OpsMx Enterprise for Spinnaker Extensions (OES) Setup Instructions

### Prerequisites

- Kubernetes cluster 1.15 or later with at least 6 cores and 20 GB memory
- Helm is setup and initialized in your Kubernetes cluster
  ```console
  $ helm version
  ```
  If helm is not setup, follow <https://helm.sh/docs/intro/install/> to install helm.

### Installing the OpsMx Enterprise for Spinnaker Extensions (OES) Spinnaker Chart

- Add opsmx helm repo to your local machine

   ```console
   $ helm repo add opsmx https://helmcharts.opsmx.com/
   ```

- Docker registry credentials is setup as a secret in Kubernetes. Before you install OES, please send an email to support@opsmx.com requesting access to the OES images with your Dockerhub id. You can proceed with installation once your Dockerhub id has been granted access.

  To be able to fetch OES docker images, username and password shall be set in values.yaml or use --set imageCredentials.username=<username> --set imageCredentials.password=<password> while running helm install.

- Your Kubernetes cluster shall support persistent volumes and loadbalancer service type.

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
`imageCredentials.username` | Username of docker account to access docker registry | `dockerID`
`imageCredentials.password` | Password of docker account | `dockerPassword`
`imageCredentials.email` | Email associated with docker account | `info@opsmx.com`
`rbac.create` | Enable or disable rbac | `true`
`installSpinnaker` | If true, install Spinnaker along with OES Extensions | `false`
`installationMode` | The installation mode. Available installation modes are **OES-AP** (both OES 3.0 and Autopilot), **OES** (Only OES 3.0), **AP** (Only Autopilot) and **None**(Skip OES installation) | `OES-AP`
`createIngress` | If true, exposes Spinnaker deck & gate services over Ingress | `false`
`k8sServiceType` | Service Type of oes-ui, oes-gate, spin-deck-ui, spin-gate | `LoadBalancer`
`installRedis` | If false, OES will uninstall its own Redis for caching | `true`
`redis.image.registry` | Registry to be used for docker images when installRedis is set to true | `docker.io`
`redis.image.repository` | Repository to be used for docker images when installRedis is set to true | `redis`
`redis.image.tag` | Tag to be used for docker images when installRedis is set to true | `true`
`redis.image.pullPolicy` | Redis image pull policy | `IfNotPresent`
`redis.url` | Set custom URL if installRedis is set to false | `redis://{{ .Release.Name }}-redis-master:6379`
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
`autopilot.image.registry` | Registry to be used for Autopilot docker images | `opsmxdev`
`autopilot.image.repository` | Repository to be used for Autopilot docker images | `ubi8-oes-autopilot`
`autopilot.image.tag` | Tag to be used for Autopilot docker images | `v3.1-202010191958`
`autopilot.image.pullPolicy` | Image pull policy for Autopilot image | `IfNotPresent`
`autopilot.config.buildAnalysis.enabled` | Set it to false to disable build analysis | `false`
`autopilot.config.ssl.enabled` | Set it to true to enable SSL | `false`
`autopilot.config.ssl.keystore` | SSL keystore value | `keystore.p12`
`autopilot.config.ssl.keyStorePassword` | SSL keystore password | `dummypwd`
`autopilot.config.ssl.keyStoreType` | SSL keystore type | `PKCS12`
`autopilot.config.ssl.keyAlias` | SSL key alias | `tomcat`
`dashboard.image.registry` | Registry to be used for dashboard images | `opsmxdev`
`dashboard.image.repository` | Repository to be used for dashboard images | `ubi8-oes-dashboard`
`dashboard.image.tag` | Tag to be used for dashboard images | `v3.1-202010192021`
`dashboard.image.pullPolicy` | Image pull policy for dashboard image | `IfNotPresent`
`gate.image.registry` | Registry to be used for OES Gate docker images | `opsmxdev`
`gate.image.repository` | Repository to be used for OES Gate docker images | `ubi8-oes-gate`
`gate.image.tag` | Tag to be used for OES Gate docker images | `v3.1-202010191958`
`gate.image.pullPolicy` | Image pull policy for OES Gate image | `IfNotPresent`
`gate.config.oesUIcors` | Regex of OES-UI URL to prevent cross origin attacks | `^https?://(?:localhost|OES_UI_LOADBALANCER_IP|opsmx.com)(?::[1-9]\d*)?/?`
`gate.config.fileBasedAuthentication` | Set it to true to disable LDAP authentication and enable file based authentication | `false`
`platform.image.registry` | Registry to be used for platform docker images | `opsmxdev`
`platform.image.repository` | Repository to be used for platform docker images | `ubi8-oes-platform`
`platform.image.tag` | Tag to be used for platform docker images | `v3.1-202010191959`
`platform.image.pullPolicy` | Image pull policy for OES platform | `IfNotPresent`
`platform.config.adminGroups` | Admin groups available | `admin, Administrators`
`platform.config.userSource` | Source of Users for authorization | `ldap`
`platform.config.supportedFeatures` | List of featues to be supported by OES | `[deployment-verification, services, releases, policies]`
`sapor.image.registry` | Registry to be used for OES SAPOR docker images | `opsmxdev`
`sapor.image.repository` | Repository to be used for OES SAPOR docker images | `ubi8-oes-sapor`
`sapor.image.tag` | Tag to be used for OES SAPOR docker images | `v3.1-202010191959`
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
`ui.image.registry` | Registry to be used for OES UI docker images | `opsmxdev`
`ui.image.repository` | Repository to be used for OES UI docker images | `ubi8-oes-ui`
`ui.image.tag` | Tag to be used for OES UI docker images | `v3.1-202010191957`
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
`installOpenLdap` | If true, installs Open LDAP server | `false`
`openldap.adminPassword` | Password to be set for admin user of LDAP | `opsmxadmin123`
`openldap.configPassword` | Password to be set for config user of LDAP | `opsmxconfig123`
`openldap.omitClusterIP` | Set to true to omit ClusterIP for openldap service | `true`
`openldap.persistence.enabled` | Enable persistent storage for open LDAP | `true`
`openldap.env.LDAP_REMOVE_CONFIG_AFTER_SETUP` | Option to remove configuration of LDAP after setup | `false`
`openldap.customLdifFiles` | Custom LDIF file for user and group creation of LDAP | ``
`ldap.enabled` | Set it to true if LDAP is to be enabled for OES | `true`
`ldap.url` | URL of LDAP server | `ldap://{{ .Release.Name }}-openldap:389`
`ldap.userDnPattern` | DN Pattern for Open LDAP | `cn={0}`
`ldap.basedn` | Base DN value | `dc=example,dc=org`
`ldap.adminDn` | Admin DN value | `cn=admin,dc=example,dc=org`
`ldap.adminPassword` | Admin password | `opsmxadmin123`
`ldap.userDisplayName` | Display name of the user | `displayName`
`ldap.pattern` | Base DN filter pattern | `(&(cn=USERNAME))`
`ldap.GroupIdentity` | User group identity | `memberOf`
`ldap.userIdentity` | User identity | `cn`
`ldap.userPrepend` | User Prepend | `cn=USERNAME`
`spinnaker.gitopsHalyardInit.enabled` | Enable gitops style halyard & account config | `false`
`spinnaker.gitopsHalyardInit.repo-type` | Repo type; git, s3, vault | `git`
`spinnaker.gitopsHalyardInit.secretName` | Secret in which git credentials shall be specified, sample secret found under templates/secrets/ | `opsmx-gitops-auth`

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

#### Connecting to OpsMx Enterprise for Spinnaker Extensions(OES)

  Once the service is up and running, find the service ip address

  	kubectl get svc oes-ui [--namespace mynamespace]

  Example output would be:

    NAME        TYPE              CLUSTER-IP      EXTERNAL-IP     PORT(S)         AGE
    oes-ui      LoadBalancer      10.0.33.110     52.149.54.222   80:30860/TCP    20m

  Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:80/

  You can login with dummysuer/dummypwd


#### Enabling centralized logging
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

## 2. Stable/Open Source Spinnaker Installation instructions

### Spinnaker Chart

[Spinnaker](http://spinnaker.io/) is an open source, multi-cloud continuous delivery platform.

#### Chart Details
This chart will provision a fully functional and fully featured Spinnaker installation
that can deploy and manage applications in the cluster that it is deployed to.

Redis and Minio are used as the stores for Spinnaker state.

For more information on Spinnaker and its capabilities, see it's [documentation](http://www.spinnaker.io/docs).

#### Installing the Chart

To install the chart with the release name `my-release`:

```bash
$ helm install --name my-release stable/spinnaker --timeout 600
```

Note that this chart pulls in many different Docker images so can take a while to fully install.

#### Configuration

Configurable values are documented in the `values.yaml`.

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```bash
$ helm install --name my-release -f values.yaml stable/spinnaker
```

> **Tip**: You can use the default [values.yaml](values.yaml)

#### Adding Kubernetes Clusters to Spinnaker

##### Configuring arbitrary clusters with a kubernetes secret
By default, installing the chart only registers the local cluster as a deploy target
for Spinnaker. If you want to add arbitrary clusters need to do the following:

1. Upload your kubeconfig to a secret with the key `config` in the cluster you are installing Spinnaker to.

```shell
$ kubectl create secret generic --from-file=$HOME/.kube/config my-kubeconfig
```

2. Set the following values of the chart:

```yaml
kubeConfig:
  enabled: true
  secretName: my-kubeconfig
  secretKey: config
  contexts:
  # Names of contexts available in the uploaded kubeconfig
  - my-context
  # This is the context from the list above that you would like
  # to deploy Spinnaker itself to.
  deploymentContext: my-context
```

##### Configuring arbitrary clusters with s3
By default, installing the chart only registers the local cluster as a deploy target
for Spinnaker. If you do not want to store your kubeconfig as a secret on the cluster, you
can also store in s3. Full documentation can be found [here](https://www.spinnaker.io/reference/halyard/secrets/s3-secrets/#secrets-in-s3).

1. Upload your kubeconfig to a s3 bucket that halyard and spinnaker services can access.


2. Set the following values of the chart:

```yaml
kubeConfig:
  enabled: true
  # secretName: my-kubeconfig
  # secretKey: config
  encryptedKubeconfig: encrypted:s3!r:us-west-2!b:mybucket!f:mykubeconfig
  contexts:
  # Names of contexts available in the uploaded kubeconfig
  - my-context
  # This is the context from the list above that you would like
  # to deploy Spinnaker itself to.
  deploymentContext: my-context
```

#### Specifying Docker Registries and Valid Images (Repositories)

Spinnaker will only give you access to Docker images that have been whitelisted, if you're using a private registry or a private repository you also need to provide credentials.  Update the following values of the chart to do so:

```yaml
dockerRegistries:
- name: dockerhub
  address: index.docker.io
  repositories:
    - library/alpine
    - library/ubuntu
    - library/centos
    - library/nginx
# - name: gcr
#   address: https://gcr.io
#   username: _json_key
#   password: '<INSERT YOUR SERVICE ACCOUNT JSON HERE>'
#   email: 1234@5678.com
# - name: ecr
#   address: <AWS-ACCOUNT-ID>.dkr.ecr.<REGION>.amazonaws.com
#   username: AWS
#   passwordCommand: aws --region <REGION> ecr get-authorization-token --output text --query 'authorizationData[].authorizationToken' | base64 -d | sed 's/^AWS://'
```

You can provide passwords as a Helm value, or you can use a pre-created secret containing your registry passwords.  The secret should have an item per Registry in the format: `<registry name>: <password>`. In which case you'll specify the secret to use in `dockerRegistryAccountSecret` like so:

```yaml
dockerRegistryAccountSecret: myregistry-secrets
```

#### Specifying persistent storage

Spinnaker supports [many](https://www.spinnaker.io/setup/install/storage/) persistent storage types. Currently, this chart supports the following:

* Azure Storage
* Google Cloud Storage
* Minio (local S3-compatible object store)
* Redis
* AWS S3

#### Use custom `cacerts`

In environments with air-gapped setup, especially with internal tooling (repos) and self-signed certificates it is required to provide an adequate `cacerts` which overrides the default one:

1. Create a yaml file `cacerts.yaml` with a secret that contanins the `cacerts`

   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: custom-cacerts
   data:
     cacerts: |
       xxxxxxxxxxxxxxxxxxxxxxx
   ```

2. Upload your `cacerts.yaml` to a secret with the key you specify in `secretName` in the cluster you are installing Spinnaker to.

   ```shell
   $ kubectl apply -f cacerts.yaml
   ```

3. Set the following values of the chart:

   ```yaml
   customCerts:
      ## Enable to override the default cacerts with your own one
      enabled: false
      secretName: custom-cacerts
   ```

#### Customizing your installation

##### Manual
While the default installation is ready to handle your Kubernetes deployments, there are
many different integrations that you can turn on with Spinnaker. In order to customize
Spinnaker, you can use the [Halyard](https://www.spinnaker.io/reference/halyard/) command line `hal`
to edit the configuration and apply it to what has already been deployed.

Halyard has an in-cluster daemon that stores your configuration. You can exec a shell in this pod to
make and apply your changes. The Halyard daemon is configured with a persistent volume to ensure that
your configuration data persists any node failures, reboots or upgrades.

For example:

```shell
$ helm install -n cd stable/spinnaker
$ kubectl exec -it cd-spinnaker-halyard-0 bash
spinnaker@cd-spinnaker-halyard-0:/workdir$ hal version list
```

##### Automated
If you have known set of commands that you'd like to run after the base config steps or if
you'd like to override some settings before the Spinnaker deployment is applied, you can enable
the `halyard.additionalScripts.enabled` flag. You will need to create a config map that contains a key
containing the `hal` commands you'd like to run. You can set the key via the config map name via `halyard.additionalScripts.configMapName` and the key via `halyard.additionalScripts.configMapKey`. The `DAEMON_ENDPOINT` environment variable can be used in your custom commands to
get a prepopulated URL that points to your Halyard daemon within the cluster. The `HAL_COMMAND` environment variable does this for you. For example:

```shell
hal --daemon-endpoint $DAEMON_ENDPOINT config security authn oauth2 enable
$HAL_COMMAND config security authn oauth2 enable
```

If you need to give halyard additional parameters when it deploys Spinnaker, you can specify them with `halyard.additionalInstallParameters`.

If you would rather the chart make the config file for you, you can set `halyard.additionalScripts.create` to `true` and then populate `halyard.additionalScripts.data.SCRIPT_NAME.sh` with the bash script you'd like to run. If you need associated configmaps or secrets you can configure those to be created as well:

```yaml
halyard:
  additionalScripts:
    create: true
    data:
      enable_oauth.sh: |-
        echo "Setting oauth2 security"
        $HAL_COMMAND config security authn oauth2 enable
  additionalSecrets:
    create: true
    data:
      password.txt: aHVudGVyMgo=
  additionalConfigMaps:
    create: true
    data:
      metadata.xml: <xml><username>admin</username></xml>
  additionalProfileConfigMaps:
    create: true
    data:
      orca-local.yml: |-
        tasks:
          useManagedServiceAccounts: true
```

Any files added through `additionalConfigMaps` will be written to disk at `/opt/halyard/additionalConfigMaps`.

##### Use a custom Halyard BOM

Spinnaker uses a Bill of Materials to describe the services that are part of a release. See the [BOM documentation](https://www.spinnaker.io/guides/operator/custom-boms/#the-bill-of-materials-bom) for more details.   

A [custom BOM](https://www.spinnaker.io/guides/operator/custom-boms/#boms-and-configuration-on-your-filesystem) can be provided to the Helm chart and used for the Halyard deployment:

```yaml
halyard:
  spinnakerVersion: '1.16.1'
  bom: |-
    artifactSources:
      debianRepository: https://dl.bintray.com/spinnaker-releases/debians
      dockerRegistry: gcr.io/spinnaker-marketplace
      gitPrefix: https://github.com/spinnaker
      googleImageProject: marketplace-spinnaker-release
    dependencies:
      consul:
        version: 0.7.5
      redis:
        version: 2:2.8.4-2
      vault:
        version: 0.7.0
    services:
      clouddriver:
        commit: 031bcec52d6c3eb447095df4251b9d7516ed74f5
        version: 6.3.0-20190904130744
      deck:
        commit: b0aac478e13a7f9642d4d39479f649dd2ef52a5a
        version: 2.12.0-20190916141821
      defaultArtifact: {}
      echo:
        commit: 7aae2141883240bd5747b981b2196adfa5b24225
        version: 2.8.0-20190914075316
      fiat:
        commit: e92cfbcac018d9dcfa03869224f7106bf2a11315
        version: 1.7.0-20190904130744
      front50:
        commit: abc5c168e3619ac084d4130eef7313cbdcfc3f61
        version: 0.19.0-20190904130744
      gate:
        commit: fd0128a6b79ddaca984c3bcdd1259c14f167cd2d
        version: 1.12.0-20190914075316
      igor:
        commit: c9bbca8e5c340d90b812f4fd27c6ebe3088dbc8d
        version: 1.6.0-20190914075316
      kayenta:
        commit: 8aa41e6e723e8d37831f5d4fe0bd5aa24ede5872
        version: 0.11.0-20190830172818
      monitoring-daemon:
        commit: 922385def92058877d61dfc835873539f0377cd7
        version: 0.15.0-20190820135930
      monitoring-third-party:
        commit: 922385def92058877d61dfc835873539f0377cd7
        version: 0.15.0-20190820135930
      orca:
        commit: 7b4e3dd6c4393ba88ebb3ea209a9c95df63e5e87
        version: 2.10.0-20190914075316
      rosco:
        commit: cfb88bb57f7af064876cfe5eef3c330a2621507b
        version: 0.14.0-20190904130744
    timestamp: '2019-09-16 18:18:44'
    version: 1.16.1
```

This will result in the specified BOM contents being written to a `1.16.1.yml` BOM file, and the Spinnaker version set to `local:1.16.1`.  

##### Set custom annotations for the halyard pod

```yaml
halyard:
  annotations:
    iam.amazonaws.com/role: <role_arn>
```

##### Set custom annotations for the halyard serviceaccount

```yaml
serviceAccount:
  serviceAccountAnnotations:
    eks.amazonaws.com/role-arn: <role_arn>
```

##### Set environment variables on the halyard pod

```yaml
halyard:
  env:
    - name: JAVA_OPTS
      value: -Dhttp.proxyHost=proxy.example.com
```
