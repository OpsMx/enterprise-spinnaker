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
  spin-gate)
    ENDPOINT_IP=""
    PORT=8084

    ## Wait for $EXTERNAL_IP_CHECK_DELAY till K8s assins a load Balancer IP to oes-gate
    check_for_loadBalancer spin-gate-np

    ## If external IP is not available
    if [ -z "$ENDPOINT_IP" ]; then
      ## Fetch the nodePort IP and replace in spinnaker.yaml
      #ENDPOINT_IP=$(kubectl get ep kubernetes -n default -o jsonpath="{.subsets[].addresses[].ip}")
      ENDPOINT_IP=$NODE_IP
      PORT=$(kubectl get svc spin-gate-np -o jsonpath="{.spec.ports[].nodePort}")
      sed -i  s/OVERRIDE_API_URL/$ENDPOINT_IP:$PORT/g /tmp/spinnaker/.hal/config
    else
      ## Substitute spin-deck external IP in spinnaker.yaml
      sed -i  s/OVERRIDE_API_URL/$ENDPOINT_IP:$PORT/g /tmp/spinnaker/.hal/config
    fi
    ;;

  spin-deck)
    ENDPOINT_IP=""
    PORT=9000

    ## Wait for $EXTERNAL_IP_CHECK_DELAY till K8s assins a load Balancer IP to oes-gate
    check_for_loadBalancer spin-deck-np

    ## If external IP is not available
    if [ -z "$ENDPOINT_IP" ]; then
      ## Fetch the nodePort & nodeport and replace in app-config.js
      ENDPOINT_IP=$NODE_IP
      PORT=$(kubectl get svc spin-deck-np -o jsonpath="{.spec.ports[].nodePort}")
      sed -i  s/OVERRIDE_DECK_URL/$ENDPOINT_IP:$PORT/g /tmp/spinnaker/.hal/config
    else
      ## Substitute oes-gate external IP in app-config.js
      sed -i  s/OVERRIDE_DECK_URL/$ENDPOINT_IP:$PORT/g /tmp/spinnaker/.hal/config
    fi
    ;;

  *)
    echo  COMP=$COMPONENT
    echo "Invalid input:$COMPONENT"
    ;;
esac
