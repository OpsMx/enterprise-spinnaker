
# Spinnaker + OpsMx Enterprise Spinnaker Extensions (OES) Setup Instructions

## Prequisites

- Kubernetes cluster 1.13 or later with at least 6 cores and 20 GB memory
- Helm is setup and initialized in your Kubernetes cluster.

		helm version

  If helm is not setup, follow <https://helm.sh/docs/using_helm/#install-helm> to install helm.

  If you are using helm v2.x, you need to initialize the Kubernetes to work with helm. If using helm v2.x, the helm version command should return both the client and server versions. If it does not return both client and server versions, you can follow these three simple steps to initialize helm v2.x in the kubernetes cluster:

		kubectl create serviceaccount -n kube-system tiller
		kubectl create clusterrolebinding tiller-binding --clusterrole=cluster-admin --serviceaccount kube-system:tiller
		helm init --service-account tiller --wait
- Docker registry credentials is setup as a secret in Kubernetes, optionally specifying the namespace OES will be deployed to

		kubectl create secret docker-registry oes-repo --docker-username=your_username --docker-password=your_password --docker-email=opsmx@example.com [--namespace mynamespace]

	The namespace must exist before you run the command. If it does not exist,

		kubectl create namespace mynamespace

  If you name your secret something other than oes-repo, you need to update the key k8sSecret in values.yaml.

	Before you install OES, please send an email to spinnaker-poc@opsmx.io requesting access to the OES images. We would require your dockerhub id to grant you access. If you do not already have a dockerhub id, you can get one at https://hub.docker.com/.

- Your Kubernetes cluster supports persistent volumes and loadbalancer service type.


## Deploying Spinnaker with OpsMx Enterprise Spinnaker Extensions (OES)


- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- Go to enterprise-spinnaker/charts/oes and deploy the chart, optionally specifying the namespace

		cd enterprise-spinnaker/charts/oes
		helm install oes . [--namespace mynamespace]

If using helm v2.x,

      helm install -n oes . [--namespace mynamespace]

## Deploying OpsMx Enterprise Spinnaker (OES) Extensions on top of existing Spinnaker

The existing Spinnaker must be running in a Kubernetes cluster and OpsMx Enterprises Extensions should be deployed
to the same namespace where Spinnaker is installed.

- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- If Gate is accessible on a name other than spin-gate within the cluster, update spinnaker.baseurl property in enterprise-spinnaker/charts/oes/config/config.properties file to the correct value.

- Go to enterprise-spinnaker/charts/oes and deploy the chart, optionally specifying the namespace where Spinnaker is already installed

      cd enterprise-spinnaker/charts/oes
      helm install oes . --set installSpinnaker=false [--namespace mynamespace]

If using helm v2.x,

      helm install -n oes . --set installSpinnaker=false [--namespace mynamespace]

## Connecting to Spinnaker and OpsMx Enterprise Enterprise Extensions

### Connecting to Spinnaker

Once the service is up and running, find the service ip address

	kubectl get svc spin-deck-ui [--namespace mynamespace]

Example output would be:

    NAME           TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
    spin-deck-ui   LoadBalancer   10.0.139.222   40.78.4.201   9000:31030/TCP   8m9s

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:9000/

### Connecting to OpsMx Enterprise Spinnaker Extensions(OES)

Once the service is up and running, find the service ip address

	kubectl get svc oes [--namespace mynamespace]

Example output would be:

    NAME   TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)                                                       AGE
    oes    LoadBalancer   10.0.4.246   34.66.226.138   8090:32097/TCP,8161:32527/TCP,9090:31265/TCP,8050:31094/TCP   9m11s

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:8161/

You can login with admin/OpsMx@123

You can change the default password during installation by updating the values.yaml or by adding this additional parameter to the helm install command:

	--set openldap.adminPassword=myPassword


### Enabling centralized logging
Spinnaker consists of multiple microservices and you need to connect to each microservice to see what is going on. OES has enabled elasticsearch, fluentbit and kibana to provide a centralized logging solution for Spinnaker. To enable it, you need to install with the flag

	  --set enableCentralLogging=true

Note, that out-of-the-box configuration of the service requires addition 2G of memory and 1 core.
To get the hostname for Kibana, run

	  kubectl get svc [--namespace mynamespace]

and find the service with kibana in the name. Example output would be:

    NAME               TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)      AGE
    somename-kibana    LoadBalancer   10.0.4.246   34.66.226.138   5601:32097   9m43s

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:5601

In Kibana, go to Discover -> Open -> Spinnaker Logs to see logs from Spinnaker pods.

### Enabling centralized monitoring
Monitoring the different services of Spinnaker is important in keeping it operating optimally. OES has enabled prometheus and grafana to provide a way to monitor Spinnaker. To enable it, you need to install with the flag

    --set enableMonitoring=true

To get the hostname for Grafana, run

    kubectl get svc [--namespace mynamespace] | grep grafana

and find the service with grafana in the name. Example output would be:

	NAME                TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)          AGE
	somename-grafana    LoadBalancer   10.28.5.38   34.68.196.3   3000:32620/TCP   10m

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:3000

The login userid will be *admin*. The get the password, run the following, replacing myname with the helm release name:

	kubectl get secret myname-grafana -o jsonpath="{.data.admin-password}"  | base64 --decode

Once you have logged in, you can go to Dashboards -> Manage and explore two dashboards that are already installed.

### Change History
Apr 2019:
- Include Prometheus, grafana

Dec 2019:
- Include Elasticsearch, fluentbit and kibana
- Make use of persistent volumes optional
- Update default Spinnaker version to 1.17.4
- Use RHEL images for OpsMx Autopilot
- Support for helm v3

Oct 2019:
- Initial version
- Installs Spinnaker, OpsMx Autopilot and openldap
