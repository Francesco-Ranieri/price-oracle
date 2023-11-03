# A Kubernetes cluster container
# In the Kubernetes Cluster:
# - Airflow
# - Spark
# - Grafana
# - MLFlow 
# - Cassandra

from diagrams import Cluster, Diagram
from diagrams.onprem.workflow import Airflow
from diagrams.onprem.analytics import Spark
from diagrams.onprem.monitoring import Grafana
from diagrams.onprem.database import Cassandra
from diagrams.onprem.mlops import Mlflow

graph_attr = {
    "fontsize": "45",
    "pad": "1.0",
    "nodesep": "1.5",
    "ranksep": "0.6",
}

with Diagram("Kubernetes Cluster", show=False, graph_attr=graph_attr):
    with Cluster("price-oracle"):
        airflow = Airflow("Airflow")
        spark = Spark("Spark")
        cassandra = Cassandra("Cassandra")
        mlflow = Mlflow("MLFlow")

    with Cluster("Visualizaton"):
        grafana = Grafana("Grafana")

    airflow >> spark
    
    airflow >> mlflow
    airflow << mlflow

    airflow >> cassandra

    grafana << cassandra
    spark << cassandra
    