import logging
import uuid
from typing import Dict, Any, List
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.membership_repository import MembershipRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import UserMembership, User, Tenant, Role

logger = logging.getLogger(__name__)


class MembershipPostgresRepository(MembershipRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            memberships = self.sql_session.session.exec(select(UserMembership)).all()

            user_ids   = list({m.user_id   for m in memberships})
            tenant_ids = list({m.tenant_id for m in memberships})
            role_ids   = list({m.role_id   for m in memberships})

            users   = {u.id: u for u in self.sql_session.session.exec(select(User).where(User.id.in_(user_ids))).all()}
            tenants = {t.id: t for t in self.sql_session.session.exec(select(Tenant).where(Tenant.id.in_(tenant_ids))).all()}
            roles   = {r.id: r for r in self.sql_session.session.exec(select(Role).where(Role.id.in_(role_ids))).all()}

            result = [
                {
                    "id":          str(m.id),
                    "user_id":     str(m.user_id),
                    "email":       users[m.user_id].email if m.user_id in users else None,
                    "full_name":   users[m.user_id].full_name if m.user_id in users else None,
                    "tenant_id":   str(m.tenant_id),
                    "tenant_name": tenants[m.tenant_id].name if m.tenant_id in tenants else None,
                    "role_id":     str(m.role_id),
                    "role_name":   roles[m.role_id].name if m.role_id in roles else None,
                    "is_active":   m.is_active,
                    "created_at":  m.created_at.isoformat() if m.created_at else None,
                }
                for m in memberships
            ]
            return Ok(result)
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            new_membership = UserMembership(
                user_id=uuid.UUID(data["user_id"]),
                tenant_id=uuid.UUID(data["tenant_id"]),
                role_id=uuid.UUID(data["role_id"]),
            )
            self.sql_session.session.add(new_membership)
            self.sql_session.session.flush()
            return Ok({
                "id":        str(new_membership.id),
                "user_id":   str(new_membership.user_id),
                "tenant_id": str(new_membership.tenant_id),
                "role_id":   str(new_membership.role_id),
            })
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.create error: {e}")
            return Err(str(e))

    def delete(self, membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            membership = self.sql_session.session.exec(
                select(UserMembership).where(UserMembership.id == uuid.UUID(membership_id))
            ).first()
            if not membership:
                return Err("MEMBERSHIP_NOT_FOUND")
            membership.is_active = False
            self.sql_session.session.add(membership)
            self.sql_session.session.flush()
            return Ok({"message": "ok", "membership_id": str(membership.id)})
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.delete error: {e}")
            return Err(str(e))

    def update(self, membership_id: str, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            membership = self.sql_session.session.exec(
                select(UserMembership).where(UserMembership.id == uuid.UUID(membership_id))
            ).first()
            if not membership:
                return Err("MEMBERSHIP_NOT_FOUND")
            membership.role_id = uuid.UUID(role_id)
            self.sql_session.session.add(membership)
            self.sql_session.session.flush()
            return Ok({
                "id":        str(membership.id),
                "user_id":   str(membership.user_id),
                "tenant_id": str(membership.tenant_id),
                "role_id":   str(membership.role_id),
                "is_active": membership.is_active,
            })
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.update error: {e}")
            return Err(str(e))

    def toggle(self, membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            membership = self.sql_session.session.exec(
                select(UserMembership).where(UserMembership.id == uuid.UUID(membership_id))
            ).first()
            if not membership:
                return Err("MEMBERSHIP_NOT_FOUND")
            membership.is_active = not membership.is_active
            self.sql_session.session.add(membership)
            self.sql_session.session.flush()
            return Ok({"membership_id": str(membership.id), "is_active": membership.is_active})
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.toggle error: {e}")
            return Err(str(e))
