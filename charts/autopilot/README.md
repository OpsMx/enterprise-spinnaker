
# OpsMx Autopilot

## Prequisites

- Kubernetes cluster 1.13 or later with at least 4 cores and 6 GB memory
- Helm is setup and initialized in your Kubernetes cluster. The following command should return both client and server version.

		helm version

  If helm is not setup, follow <https://helm.sh/docs/using_helm/#install-helm> to install helm. If you use the Google or Azure cloud shell, they already have helm installed on it. You can follow these three simple steps to initialize helm(v2) in the kubernetes cluster. In case helm v3 is installed, skip below steps.

		kubectl create serviceaccount -n kube-system tiller
		kubectl create clusterrolebinding tiller-binding --clusterrole=cluster-admin --serviceaccount kube-system:tiller
		helm init --service-account tiller --wait

- If autopilot is to be deployed to a specific namespace, the namespace must exist before you run the command. If it does not exist,

		kubectl create namespace <mynamespace>

- Your Kubernetes cluster supports persistent volumes and loadbalancer service type

## Deploying Autopilot

- Clone the OpsMx Enterprise Spinnaker github repository

		git clone https://github.com/OpsMx/enterprise-spinnaker.git

- Go to enterprise-spinnaker/charts/autopilot and deploy the chart, optionally specifying the namespace

  Update the necessary parameters in values.yaml or use --set option while running helm install.
  To be able to fetch Autopilot docker images, username and password shall be set in values.yaml or use --set imageCredentials.username=<username> --set imageCredentials.password=<password> while running helm install.

  Before you install Autopilot, please send an email to support@opsmx.com requesting access to the Autopilot images with your Dockerhub id. You can proceed with installation once your Dockerhub id has been granted access.

		cd enterprise-spinnaker/charts/autopilot
  For helm v2, install using:
    		helm install -n autopilot . [--namespace mynamespace]
    		helm install -n autopilot . [--namespace mynamespace] --set imageCredentials.username=<username> --set imageCredentials.password=<password>

  For helm v3, install using:
    		helm install -n autopilot . [--namespace mynamespace]
    		helm install autopilot . [--namespace mynamespace] --set imageCredentials.username=<username> --set imageCredentials.password=<password>


## Connecting to Autopilot

Once the service is up and running, find the service ip address

    		kubectl get svc autopilot [--namespace mynamespace]

Example output would be:

    NAME         TYPE           CLUSTER-IP   EXTERNAL-IP     PORT(S)                                        AGE
    autopilot    LoadBalancer   10.0.4.246   34.66.226.138   8090:32097/TCP,8161:32527/TCP,9090:31265/TCP   9m11s

Now, UI can be accessed via EXTERNAL-IP address, go to http://<EXTERNAL-IP>:8161/
