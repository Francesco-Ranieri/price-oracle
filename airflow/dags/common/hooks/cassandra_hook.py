from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models.connection import Connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from cassandra.query import BatchStatement

import logging

logger = logging.getLogger(__name__)

class CassandraHook:
    def __init__(self, cassandra_conn_id: str = "cassandra_default") -> None:
        self.MAX_QUERY_IN_BATCH = 16384
        self.cassandra_conn_id = cassandra_conn_id
        self.session = self.get_conn()

    def get_conn(self) -> Session:
        conn = CassandraHook.get_connection(self.cassandra_conn_id)
        cluster = Cluster(
            contact_points=conn.host.split(","),
            port=conn.port,
            auth_provider=PlainTextAuthProvider(
                username=conn.login, password=conn.password
            ),
        )
        session = cluster.connect()
        session.set_keyspace(conn.schema)
        return session


    @classmethod
    def get_connection(cls, conn_id: str) -> Connection:
        conn = BaseHook.get_connection(conn_id)
        if not conn.host:
            raise AirflowException(
                f"Missing hostname (host) for connection '{conn.conn_id}'"
            )
        if not conn.port:
            raise AirflowException(
                f"Missing port (port) for connection '{conn.conn_id}'"
            )
        if not conn.login:
            raise AirflowException(
                f"Missing username (login) for connection '{conn.conn_id}'"
            )
        if not conn.password:
            raise AirflowException(
                f"Missing password (password) for connection '{conn.conn_id}'"
            )
        return conn


    def run_query(self, query: str, parameters: dict = None) -> None:
        prepared = self.session.prepare(query)
        return self.session.execute(prepared, parameters=parameters)


    def run_batch_query(self, query: str, parameters: list = None) -> None:
        """
        Cassandra has a hard limit of 65535 queries in a batch. 
        To avoid timeouts, we will use a batch size of 16384.
        """

        logger.info(f"Running batch query with {len(parameters)} parameters")
        if len(parameters) > self.MAX_QUERY_IN_BATCH:
            logger.info(f"Batch query will be split into {len(parameters) // self.MAX_QUERY_IN_BATCH} batches")

        prepared = self.session.prepare(query)

        # Splice the parameters into multiple batches if it exceeds the maximum query size
        if parameters:
            for i in range(0, len(parameters), self.MAX_QUERY_IN_BATCH):
                self._run_batch_query(prepared, parameters[i : i + self.MAX_QUERY_IN_BATCH])
        else:
            raise AirflowException("Parameters cannot be empty")

    
    def _run_batch_query(self, query: str, parameters: list = None) -> None:
        batch = BatchStatement()
        for param in parameters:
            batch.add(query, param)

        logger.info(f"Executing batch query with {len(batch)} queries")
        self.session.execute(batch)
        logger.info("Batch query executed successfully")