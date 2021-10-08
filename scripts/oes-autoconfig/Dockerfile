FROM alpine/k8s:1.18.16
ADD config_endpoint.sh /home/
RUN apk add jq gettext
RUN wget https://github.com/mikefarah/yq/releases/download/v4.2.0/yq_linux_amd64.tar.gz -O - |\
  tar xz && mv yq_linux_amd64 /usr/bin/yq
