#!/bin/bash -x

if [ $# -gt 1 ]
then
   echo "Invalid input, only one argument expected"
   exit
fi

COMPONENT=$1
EXTERNAL_IP_CHECK_DELAY=$EXTERNAL_IP_CHECK_DELAY

check_for_loadBalancer()
{
    ## Wait for $EXTERNAL_IP_CHECK_DELAY till K8s assins a load Balancer IP to oes-gate
    iter=0
    lapsedTime=0
    while [ $iter -lt 100 ]
    do
      ENDPOINT_IP=$(kubectl get svc $1 -o jsonpath="{.status.loadBalancer.ingress[].ip}")
      if [ ! -z "$ENDPOINT_IP" ];
      then
        echo "Found LoadBalancer IP for" $1
        break
      fi
      sleep 5
      lapsedTime=`expr $lapsedTime + 5`
      if [ $lapsedTime -gt $EXTERNAL_IP_CHECK_DELAY ];
      then
	echo "Time Lapsed" $lapsedTime
        echo "Timeout! Fetching nodeport IP alternatively"
        break
      fi
      echo "Time Lapsed" $lapsedTime
      iter=`expr $iter + 1`
    done
}

case "$COMPONENT" in
  oes-ui)
    cp /config/* /var/www/html/assets/config/

    ENDPOINT_IP=""

    ## Wait for $EXTERNAL_IP_CHECK_DELAY till K8s assins a load Balancer IP to oes-gate
    check_for_loadBalancer oes-gate

    ## If external IP is not available
    if [ -z "$ENDPOINT_IP" ]; then
      echo "Gate LB endpoint is empty"
    else
      ## Substitute oes-gate external IP in app-config.js
      cat /var/www/html/assets/config/app-config.json | jq ".endPointUrl = \"http://$ENDPOINT_IP:8084/\"" > /var/www/html/assets/config/app-config-temp.json
      mv /var/www/html/assets/config/app-config-temp.json /var/www/html/assets/config/app-config.json
    fi
    ;;
  oes-gate)
    cp /config/* /opt/spinnaker/config/

    ENDPOINT_IP=""

    ## Wait for $EXTERNAL_IP_CHECK_DELAY till K8s assins a load Balancer IP to oes-ui
    check_for_loadBalancer oes-ui

    ## If external IP is not available
    if [ -z "$ENDPOINT_IP" ]; then
      echo "UI LB endpoint is empty"
    else
      ## Substitute oes-ui external IP in gate.yml uner allowed-origin-patterns
      EXISTING_CORS=$(cat /opt/spinnaker/config/gate.yml | yq e '.cors.allowed-origins-pattern' -)
      export NEW_CORS=$(echo $EXISTING_CORS | sed "s/|/|$ENDPOINT_IP|/")
      check_for_loadBalancer spin-deck-lb
      if [ ! -z "$ENDPOINT_IP" ]; then
        export NEW_CORS=$(echo $NEW_CORS | sed "s/|/|$ENDPOINT_IP|/")
      fi
      echo "New cors is "$NEW_CORS
      yq e '.cors.allowed-origins-pattern = "${NEW_CORS}"' /opt/spinnaker/config/gate.yml | tee /opt/spinnaker/config/gate-temp.yml
      envsubst < /opt/spinnaker/config/gate-temp.yml > /opt/spinnaker/config/gate.yml
      rm -rf /opt/spinnaker/config/gate-temp.yml
    fi
    ;;

  *)
    echo  COMP=$COMPONENT
    echo "Invalid input:$COMPONENT"
    ;;
esac
