import logging
import uuid
from typing import Dict, Any, List
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.tenant_repository import TenantRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import Tenant

logger = logging.getLogger(__name__)


class TenantPostgresRepository(TenantRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            rows = self.sql_session.session.exec(
                select(Tenant).order_by(Tenant.name)
            ).all()
            tenants = [
                {
                    "id": str(t.id),
                    "slug": t.slug,
                    "name": t.name,
                    "redirect_url": t.redirect_url,
                    "is_active": t.is_active,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in rows
            ]
            return Ok(tenants)
        except Exception as e:
            logger.error(f"TenantPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, tenant_id: str) -> Result[Dict[str, Any], str]:
        try:
            tenant = self.sql_session.session.exec(
                select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
            ).first()
            if not tenant:
                return Err("TENANT_NOT_FOUND")
            return Ok({
                "id": str(tenant.id),
                "slug": tenant.slug,
                "name": tenant.name,
                "redirect_url": tenant.redirect_url,
                "is_active": tenant.is_active,
            })
        except Exception as e:
            logger.error(f"TenantPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            new_tenant = Tenant(
                slug=data["slug"],
                name=data["name"],
                redirect_url=data["redirect_url"],
            )
            self.sql_session.session.add(new_tenant)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_tenant.id),
                "slug": new_tenant.slug,
                "name": new_tenant.name,
                "redirect_url": new_tenant.redirect_url,
            })
        except Exception as e:
            logger.error(f"TenantPostgresRepository.create error: {e}")
            return Err(str(e))
