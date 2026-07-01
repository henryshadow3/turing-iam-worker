import logging
import uuid
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.role_repository import RoleRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import Role, Tenant

logger = logging.getLogger(__name__)


class RolePostgresRepository(RoleRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_by_tenant(self, tenant_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            if tenant_id:
                roles = self.sql_session.session.exec(
                    select(Role).where(Role.tenant_id == uuid.UUID(tenant_id)).order_by(Role.name)
                ).all()
            else:
                roles = self.sql_session.session.exec(
                    select(Role).order_by(Role.name)
                ).all()

            tenant_ids = list({r.tenant_id for r in roles})
            tenants = self.sql_session.session.exec(
                select(Tenant).where(Tenant.id.in_(tenant_ids))
            ).all()
            tenant_name_map = {t.id: t.name for t in tenants}

            result = [
                {
                    "id": str(r.id),
                    "tenant_id": str(r.tenant_id),
                    "name": r.name,
                    "is_active": r.is_active,
                    "tenant_name": tenant_name_map.get(r.tenant_id),
                }
                for r in roles
            ]
            return Ok(result)
        except Exception as e:
            logger.error(f"RolePostgresRepository.list_by_tenant error: {e}")
            return Err(str(e))

    def get_by_id(self, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            role = self.sql_session.session.exec(
                select(Role).where(Role.id == uuid.UUID(role_id))
            ).first()
            if not role:
                return Err("ROLE_NOT_FOUND")
            return Ok({
                "id": str(role.id),
                "tenant_id": str(role.tenant_id),
                "name": role.name,
                "is_active": role.is_active,
            })
        except Exception as e:
            logger.error(f"RolePostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            new_role = Role(
                tenant_id=uuid.UUID(data["tenant_id"]),
                name=data["name"],
            )
            self.sql_session.session.add(new_role)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_role.id),
                "tenant_id": str(new_role.tenant_id),
                "name": new_role.name,
            })
        except Exception as e:
            logger.error(f"RolePostgresRepository.create error: {e}")
            return Err(str(e))
