import logging
import uuid
from typing import Dict, Any, List
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.application_repository import ApplicationRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import Application

logger = logging.getLogger(__name__)


class ApplicationPostgresRepository(ApplicationRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            apps = self.sql_session.session.exec(
                select(Application).order_by(Application.name)
            ).all()
            return Ok([
                {
                    "id": str(a.id),
                    "slug": a.slug,
                    "name": a.name,
                    "is_active": a.is_active,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in apps
            ])
        except Exception as e:
            logger.error(f"ApplicationPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, application_id: str) -> Result[Dict[str, Any], str]:
        try:
            app = self.sql_session.session.exec(
                select(Application).where(Application.id == uuid.UUID(application_id))
            ).first()
            if not app:
                return Err("APPLICATION_NOT_FOUND")
            return Ok({
                "id": str(app.id),
                "slug": app.slug,
                "name": app.name,
                "is_active": app.is_active,
            })
        except Exception as e:
            logger.error(f"ApplicationPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def toggle(self, application_id: str) -> Result[Dict[str, Any], str]:
        try:
            app = self.sql_session.session.exec(
                select(Application).where(Application.id == uuid.UUID(application_id))
            ).first()
            if not app:
                return Err("APPLICATION_NOT_FOUND")
            app.is_active = not app.is_active
            self.sql_session.session.add(app)
            self.sql_session.session.flush()
            return Ok({"application_id": str(app.id), "is_active": app.is_active})
        except Exception as e:
            logger.error(f"ApplicationPostgresRepository.toggle error: {e}")
            return Err(str(e))
