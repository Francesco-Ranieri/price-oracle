# big-data
Big Data exam


## Instructions

helm repo add apache-airflow https://airflow.apache.org
helm repo add apache-cassandra oci://registry-1.docker.io/bitnamicharts
helm repo add grafana https://grafana.github.io/helm-charts

## RUN
skaffold dev
skaffold dev --status-check=false
