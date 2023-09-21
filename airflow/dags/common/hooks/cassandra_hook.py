from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models.connection import Connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session


class CassandraHook:
    def __init__(self, cassandra_conn_id: str = "cassandra_default") -> None:
        self.cassandra_conn_id = cassandra_conn_id

    def get_conn(self) -> Session:
        conn = self.get_connection(self.cassandra_conn_id)
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

    def get_connection(self, conn_id: str) -> Connection:
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
        with self.get_conn() as session:
            session.execute(query, parameters=parameters)
