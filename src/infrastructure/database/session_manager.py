import logging
import psycopg2

logger = logging.getLogger(__name__)


class SQLSessionManager:
    def __init__(self, settings):
        self.settings = settings
        self._connection = None

    def get_connection(self):
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                dbname=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
            )
        return self._connection

    def close(self):
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
            logger.info("PostgreSQL connection closed")
