# Instructions

Please follow these instructions to get the logs all ISD Services and Number of Users logged in ISD, Number of Applications,Pipelines,Cloud Targets and Number of Pipelines executed per day.

Create secrets mentioned below.**NOTE**: You only need to create these secrets if they are changed from the default
   - `kubectl -n opsmx-isd create secret generic ldappassword --from-literal ldappassword=PUT_YOUR_SECRET_HERE` (ldappassword value must be which password which is used for login to isd)
   - `kubectl -n opsmx-isd create secret generic redispassword --from-literal redispassword=PUT_YOUR_SECRET_HERE` (Default value is password)

Read the comments in the yaml file and Execute below commands, by repalcing the namespace

- `kubectl -n opsmx-isd apply -f isdinfo-inputcm.yaml` # Read the comments in the yaml and apply 
- `kubectl -n opsmx-isd apply -f serviceaccount.yaml` # Edit namespace if changed from the default "opsmx-isd"
- `kubectl -n opsmx-isd apply -f job.yaml` # Change the namespace accordingly default is "opsmx-isd"

    - Once pod will completed so please check the pod logs to verify the logs are publised to opsmx-jfrog or not.

      `kubectl -n opsmx-isd logs isd-info-xxx` #Replacing the name of the pod name correctly
