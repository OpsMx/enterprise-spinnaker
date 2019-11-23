
# OpsMx Enterprise Spinnaker (OES)

## Prequisites

- Kubernetes cluster 1.13 or later with at least 4 cores and 6 GB memory
- Helm is setup and initialized in your Kubernetes cluster. The following command should return both client and server version.

		helm version

  If helm is not setup, follow <https://helm.sh/docs/using_helm/#install-helm> to install helm. If you use the Google or Azure cloud shell, they already have helm installed on it. You can follow these three simple steps to initialize helm in the kubernetes cluster.

		kubectl create serviceaccount -n kube-system tiller
		kubectl create clusterrolebinding tiller-binding --clusterrole=cluster-admin --serviceaccount kube-system:tiller
		helm init --service-account tiller --wait
- Docker registry credentials is setup as a secret in Kubernetes, optionally specifying the namespace OES will be deployed to

		kubectl create secret docker-registry oes-repo --docker-username=your_username --docker-password=your_password --docker-email=opsmx@example.com [--namespace mynamespace]

	The namespace must exist before you run the command. If it does not exist,

		kubectl create namespace mynamespace

  If you name your secret something other than oes-repo, you need to update the key k8sSecret in values.yaml.

	Before you install OES, please send an email to support@opsmx.com requesting access to the OES images with your Dockerhub id. You can proceed with installation your Dockerhub id has been granted access.
- Your Kubernetes cluster supports persistent volumes and loadbalancer service type

## Deploying Autopilot

- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- Go to enterprise-spinnaker/charts/autopilot and deploy the chart, optionally specifying the namespace

		cd enterprise-spinnaker/charts/autopilot
    helm install -n autopilot . [--namespace mynamespace]
		

## Connecting to Autopilot

Once the service is up and running, find the service ip address

	kubectl get svc oes [--namespace mynamespace]

Example output would be:

    NAME   TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)                                                       AGE
    oes    LoadBalancer   10.0.4.246   34.66.226.138   8090:32097/TCP,8161:32527/TCP,9090:31265/TCP,8050:31094/TCP   9m11s

Using the EXTERNAL-IP address, go to http://EXTERNAL-IP:8161/
