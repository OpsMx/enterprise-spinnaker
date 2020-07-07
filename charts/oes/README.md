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


## Deploying OpsMx Enterprise Spinnaker Extensions (OES) Spinnaker


- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- Docker registry credentials is setup as a secret in Kubernetes. Before you install Autopilot, please send an email to support@opsmx.com requesting access to the Autopilot images with your Dockerhub id. You can proceed with installation once your Dockerhub id has been granted access.

  To be able to fetch Autopilot docker images, username and password shall be set in values.yaml or use --set imageCredentials.username=<username> --set imageCredentials.password=<password> while running helm install.

- Your Kubernetes cluster supports persistent volumes and loadbalancer service type.

- Go to enterprise-spinnaker/charts/oes and deploy the chart, optionally specifying the namespace

  The namespace must exist before you run the command. If it does not exist,

		kubectl create namespace mynamespace

		cd enterprise-spinnaker/charts/oes
		helm install oes . [--namespace mynamespace]

For helm v2, install using: helm install -n oes . --set imageCredentials.username= --set imageCredentials.password= [--namespace mynamespace]

For helm v3, install using: helm install oes . --set imageCredentials.username= --set imageCredentials.password= [--namespace mynamespace]

## Deploying OpsMx Enterprise Spinnaker (OES) Extensions on top of existing Spinnaker

The existing Spinnaker must be running in a Kubernetes cluster and OpsMx Enterprises Extensions should be deployed
to the same namespace where Spinnaker is installed.

- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- If Gate is accessible on a name other than spin-gate within the cluster, update spinGateURL property in enterprise-spinnaker/charts/oes/values.yaml file to the correct value.

- Go to enterprise-spinnaker/charts/oes and deploy the chart, optionally specifying the namespace where Spinnaker is already installed

      cd enterprise-spinnaker/charts/oes
      Update the values.yaml file with the below details (to install OES with Spinnaker)
      spinuser     # Spinnker login User name
      spinpasswd   # Spinnker login User Password
      oesGateURL   # OES Gate URL
      oesUIcors    # Value of the OES UI URL Regex
      spinGateURL  # Spinnaker Gate URL
      spinExternalGateURL ## Value of the Spinnaker URL to access spinnaker from UI

      helm install oes . --set installSpinnaker=false --set installRedis=true --set imageCredentials.username= --set imageCredentials.password= [--namespace mynamespace]

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

	kubectl get svc oes-ui [--namespace mynamespace]

Example output would be:

NAME   							TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)          AGE
oes-ui-svc       LoadBalancer     10.0.33.110  52.149.54.222   80:30860/TCP      20h

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:80/

You can login with dummysuer/dummypwd


### Enabling centralized logging
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


### Change History
Dec 2019:
- Include Elasticsearch, fluentbit and kibana
- Make use of persistent volumes optional
- Update default Spinnaker version to 1.17.4
- Use RHEL images for OpsMx Autopilot
- Support for helm v3

Oct 2019:
- Initial version
- Installs Spinnaker, OpsMx Autopilot and openldap
