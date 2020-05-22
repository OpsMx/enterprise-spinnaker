for obj in deploy sts svc job Secret ConfigMap pvc pv role clusterrole ; do kubectl get $obj | grep -v NAME | grep -i spin | awk '{print $1}' | xargs kubectl delete $obj; done

