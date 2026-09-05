import logging
import uuid
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.role_repository import RoleRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import Role, Tenant, Application

logger = logging.getLogger(__name__)

# Roles cuyo nombre autoriza como admin del tenant (dashboard-back ADMIN_ROLES).
# Desactivarlos dejaría al tenant sin administradores (lockout).
PROTECTED_ROLE_NAMES = ("admin", "administrador")


class RolePostgresRepository(RoleRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_by_tenant(self, tenant_id: Optional[str] = None,
                        application_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            stmt = select(Role)
            if tenant_id:
                stmt = stmt.where(Role.tenant_id == uuid.UUID(tenant_id))
            if application_id:
                stmt = stmt.where(Role.application_id == uuid.UUID(application_id))
            roles = self.sql_session.session.exec(stmt.order_by(Role.name)).all()

            tenant_ids = list({r.tenant_id for r in roles if r.tenant_id})
            tenants = self.sql_session.session.exec(
                select(Tenant).where(Tenant.id.in_(tenant_ids))
            ).all() if tenant_ids else []
            tenant_name_map = {t.id: t.name for t in tenants}

            application_ids = list({r.application_id for r in roles if r.application_id})
            applications = self.sql_session.session.exec(
                select(Application).where(Application.id.in_(application_ids))
            ).all() if application_ids else []
            application_map = {a.id: a for a in applications}

            result = []
            for r in roles:
                app = application_map.get(r.application_id) if r.application_id else None
                if r.tenant_id is None and r.application_id is not None:
                    scope = "catalog"
                elif r.tenant_id is not None and r.application_id is not None:
                    scope = "custom"
                else:
                    scope = "legacy"
                result.append({
                    "id": str(r.id),
                    "tenant_id": str(r.tenant_id) if r.tenant_id else None,
                    "name": r.name,
                    "is_active": r.is_active,
                    "tenant_name": tenant_name_map.get(r.tenant_id),
                    "application_id": str(r.application_id) if r.application_id else None,
                    "application_slug": app.slug if app else None,
                    "application_name": app.name if app else None,
                    "scope": scope,
                })
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
                "tenant_id": str(role.tenant_id) if role.tenant_id else None,
                "name": role.name,
                "is_active": role.is_active,
                "application_id": str(role.application_id) if role.application_id else None,
            })
        except Exception as e:
            logger.error(f"RolePostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        """Crea un rol en el modelo híbrido (ADR 0001 §4/§5, migración 017).

        `tenant_id` es opcional cuando `application_id` viene poblado (rol de
        catálogo, compartido por todos los tenants con esa app habilitada).
        La validación de las 3 combinaciones válidas ya ocurrió en
        role_create_action; aquí solo se persiste. El CHECK roles_scope_chk
        de BD es la última línea de defensa si algún llamador se salta la
        action.
        """
        try:
            tenant_id = data.get("tenant_id")
            application_id = data.get("application_id")
            new_role = Role(
                tenant_id=uuid.UUID(tenant_id) if tenant_id else None,
                application_id=uuid.UUID(application_id) if application_id else None,
                name=data["name"],
            )
            self.sql_session.session.add(new_role)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_role.id),
                "tenant_id": str(new_role.tenant_id) if new_role.tenant_id else None,
                "application_id": str(new_role.application_id) if new_role.application_id else None,
                "name": new_role.name,
                "is_active": new_role.is_active,
            })
        except Exception as e:
            logger.error(f"RolePostgresRepository.create error: {e}")
            return Err(str(e))

    def toggle(self, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            role = self.sql_session.session.exec(
                select(Role).where(Role.id == uuid.UUID(role_id))
            ).first()
            if not role:
                return Err("ROLE_NOT_FOUND")
            if role.is_active and role.name.lower() in PROTECTED_ROLE_NAMES:
                return Err("CANNOT_DISABLE_ADMIN_ROLE")
            role.is_active = not role.is_active
            self.sql_session.session.add(role)
            self.sql_session.session.flush()
            return Ok({
                "role_id":   str(role.id),
                "name":      role.name,
                "is_active": role.is_active,
            })
        except Exception as e:
            logger.error(f"RolePostgresRepository.toggle error: {e}")
            return Err(str(e))
