import logging

from cassandra.cluster import Session
from common.hooks.cassandra_hook import CassandraHook
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

class SparkHook:

    def __init__(
        self,
        app_name: str = "CassandraSpark",
        master: str = "spark://price-oracle-spark-master-svc:7077",
    ):
        self.app_name = app_name
        self.master = master
   
    def get_spark_session(self):
        spark_session = SparkSession.builder \
            .appName(self.app_name) \
            .master(self.master) \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
            .getOrCreate()
        
        return spark_session
    

    def get_spark_cassandra_session(self, conn_id: str = "cassandra_default") -> Session:
        """
        Get a connection to Cassandra
        """
        self.cassandra_connection = CassandraHook.get_connection(conn_id=conn_id)
        spark_session = SparkSession.builder \
            .appName(self.app_name) \
            .master(self.master) \
            .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
            .config("spark.cassandra.connection.host", self.cassandra_connection.host) \
            .config("spark.cassandra.auth.username", self.cassandra_connection.login) \
            .config("spark.cassandra.auth.password", self.cassandra_connection.password) \
            .getOrCreate()
        
        return spark_session