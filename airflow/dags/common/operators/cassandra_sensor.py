# Sensor class to wait for Cassandra to be ready

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from common.hooks.cassandra_hook import CassandraHook


class CassandraSensor(BaseSensorOperator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cassandra_hook = CassandraHook()

    def poke(self, context):
        self.log.info("Poking Cassandra")
        try:
            self.cassandra_hook.run_query("SELECT now() FROM system.local")
            return True
        except Exception as e:
            self.log.info(f"Cassandra is not ready yet: {e}")
            raise AirflowException(f"Cassandra is not ready yet: {e}")
