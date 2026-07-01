from sqlmodel import create_engine, Session as SQLModelSession
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)

_engine = None


def _get_engine(settings):
    global _engine
    if _engine is None:
        dsn = (
            f"postgresql+psycopg2://{quote_plus(settings.postgres_user)}:"
            f"{quote_plus(settings.postgres_password)}@{settings.postgres_host}:"
            f"{settings.postgres_port}/{settings.postgres_db}"
        )
        _engine = create_engine(dsn)
    return _engine


class SQLSessionManager:
    def __init__(self, settings):
        self._engine = _get_engine(settings)
        self._session = None

    @property
    def session(self) -> SQLModelSession:
        return self._session

    def __enter__(self):
        self._session = SQLModelSession(self._engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None or self._session.get_transaction() is None:
                self._session.rollback()
            else:
                try:
                    self._session.commit()
                except Exception:
                    self._session.rollback()
                    raise
        except Exception as e:
            logger.error(f"Error during SQL session close: {e}")
            raise
        finally:
            self._session.close()
        return False

    def close(self):
        if self._session:
            self._session.close()
