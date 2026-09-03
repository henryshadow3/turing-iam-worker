import logging
import uuid
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.tenant_application_repository import TenantApplicationRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import TenantApplication, Tenant, Application

logger = logging.getLogger(__name__)


class TenantApplicationPostgresRepository(TenantApplicationRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def _enrich(self, rows: List[TenantApplication]) -> List[Dict[str, Any]]:
        tenant_ids = list({r.tenant_id for r in rows})
        app_ids    = list({r.application_id for r in rows})

        tenants = {t.id: t for t in self.sql_session.session.exec(
            select(Tenant).where(Tenant.id.in_(tenant_ids))
        ).all()} if tenant_ids else {}
        apps = {a.id: a for a in self.sql_session.session.exec(
            select(Application).where(Application.id.in_(app_ids))
        ).all()} if app_ids else {}

        return [
            {
                "id": str(r.id),
                "tenant_id": str(r.tenant_id),
                "tenant_slug": tenants[r.tenant_id].slug if r.tenant_id in tenants else None,
                "application_id": str(r.application_id),
                "application_slug": apps[r.application_id].slug if r.application_id in apps else None,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    def list_all(self, tenant_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            if tenant_id:
                rows = self.sql_session.session.exec(
                    select(TenantApplication).where(TenantApplication.tenant_id == uuid.UUID(tenant_id))
                ).all()
            else:
                rows = self.sql_session.session.exec(select(TenantApplication)).all()
            return Ok(self._enrich(rows))
        except Exception as e:
            logger.error(f"TenantApplicationPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, tenant_application_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(TenantApplication).where(TenantApplication.id == uuid.UUID(tenant_application_id))
            ).first()
            if not row:
                return Err("TENANT_APPLICATION_NOT_FOUND")
            enriched = self._enrich([row])
            return Ok(enriched[0])
        except Exception as e:
            logger.error(f"TenantApplicationPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            tenant_id = uuid.UUID(data["tenant_id"])
            application_id = uuid.UUID(data["application_id"])

            tenant = self.sql_session.session.exec(
                select(Tenant).where(Tenant.id == tenant_id)
            ).first()
            if not tenant:
                return Err("TENANT_NOT_FOUND")
            application = self.sql_session.session.exec(
                select(Application).where(Application.id == application_id)
            ).first()
            if not application:
                return Err("APPLICATION_NOT_FOUND")

            existing = self.sql_session.session.exec(
                select(TenantApplication).where(
                    TenantApplication.tenant_id == tenant_id,
                    TenantApplication.application_id == application_id,
                )
            ).first()
            if existing:
                return Err("TENANT_APPLICATION_ALREADY_EXISTS")

            new_row = TenantApplication(tenant_id=tenant_id, application_id=application_id)
            self.sql_session.session.add(new_row)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_row.id),
                "tenant_id": str(new_row.tenant_id),
                "application_id": str(new_row.application_id),
                "is_active": new_row.is_active,
            })
        except Exception as e:
            logger.error(f"TenantApplicationPostgresRepository.create error: {e}")
            return Err(str(e))

    def toggle(self, tenant_application_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(TenantApplication).where(TenantApplication.id == uuid.UUID(tenant_application_id))
            ).first()
            if not row:
                return Err("TENANT_APPLICATION_NOT_FOUND")
            row.is_active = not row.is_active
            self.sql_session.session.add(row)
            self.sql_session.session.flush()
            return Ok({"tenant_application_id": str(row.id), "is_active": row.is_active})
        except Exception as e:
            logger.error(f"TenantApplicationPostgresRepository.toggle error: {e}")
            return Err(str(e))
