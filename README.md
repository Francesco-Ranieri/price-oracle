# big-data
Big Data exam


## Instructions

helm repo add apache-airflow https://airflow.apache.org
helm repo add apache-cassandra oci://registry-1.docker.io/bitnamicharts
helm repo add grafana https://grafana.github.io/helm-charts

## RUN
skaffold dev
skaffold dev --status-check=false

## TO DEBUG DAGS:
1) Install airflow on your host machine
2) Edit the `airflow.cfg` file (~/airflow/airflow.cfg) and set `allowed_deserialization_classes` to `common\..*`. 
3) Run `airflow connections add cassandra_default --conn-uri cassandra://cassandra:l1Lc%C2%A3C9eKFR5@localhost:9042/mykeyspace`
4) Run `airflow db migrate`
5) Debug the dag file as usual


## DATA

https://www.cryptodatadownload.com/data/cexio/