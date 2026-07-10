import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import (
    AccessRequest, UserMembership, User, Tenant, Role,
)

logger = logging.getLogger(__name__)


class AccessRequestPostgresRepository:
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_by_status(self, status: Optional[str]) -> Result[List[Dict[str, Any]], str]:
        try:
            query = select(AccessRequest)
            if status:
                query = query.where(AccessRequest.status == status)
            query = query.order_by(AccessRequest.created_at.desc())
            requests = self.sql_session.session.exec(query).all()

            user_ids   = list({r.user_id   for r in requests})
            tenant_ids = list({r.tenant_id for r in requests})
            role_ids   = list({r.requested_role_id for r in requests if r.requested_role_id})

            users   = {u.id: u for u in self.sql_session.session.exec(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
            tenants = {t.id: t for t in self.sql_session.session.exec(select(Tenant).where(Tenant.id.in_(tenant_ids))).all()} if tenant_ids else {}
            roles   = {r.id: r for r in self.sql_session.session.exec(select(Role).where(Role.id.in_(role_ids))).all()} if role_ids else {}

            result = [
                {
                    "id":                str(r.id),
                    "user_id":           str(r.user_id),
                    "email":             users[r.user_id].email if r.user_id in users else None,
                    "full_name":         users[r.user_id].full_name if r.user_id in users else None,
                    "tenant_id":         str(r.tenant_id),
                    "tenant_name":       tenants[r.tenant_id].name if r.tenant_id in tenants else None,
                    "requested_role_id": str(r.requested_role_id) if r.requested_role_id else None,
                    "requested_role_name": roles[r.requested_role_id].name if r.requested_role_id in roles else None,
                    "status":            r.status,
                    "note":              r.note,
                    "created_at":        r.created_at.isoformat() if r.created_at else None,
                    "resolved_at":       r.resolved_at.isoformat() if r.resolved_at else None,
                }
                for r in requests
            ]
            return Ok(result)
        except Exception as e:
            logger.error(f"AccessRequestPostgresRepository.list_by_status error: {e}")
            return Err(str(e))

    def approve(self, request_id: str, role_id: Optional[str], resolved_by: Optional[str]) -> Result[Dict[str, Any], str]:
        """Aprueba la solicitud: crea la membresía y marca la solicitud como aprobada.

        role_id opcional: si no se pasa, usa el rol sugerido de la solicitud.
        Reactiva la membresía si ya existía inactiva (respeta UNIQUE user+tenant).
        """
        try:
            session = self.sql_session.session
            req = session.exec(
                select(AccessRequest).where(AccessRequest.id == uuid.UUID(request_id))
            ).first()
            if not req:
                return Err("REQUEST_NOT_FOUND")
            if req.status != "pending":
                return Err("REQUEST_ALREADY_RESOLVED")

            final_role_id = role_id or (str(req.requested_role_id) if req.requested_role_id else None)
            if not final_role_id:
                return Err("MISSING_ROLE_ID")

            # ¿Ya existe membresía en ese tenant? (UNIQUE user_id, tenant_id)
            existing = session.exec(
                select(UserMembership).where(
                    UserMembership.user_id == req.user_id,
                    UserMembership.tenant_id == req.tenant_id,
                )
            ).first()

            if existing:
                existing.role_id = uuid.UUID(final_role_id)
                existing.is_active = True
                session.add(existing)
                membership_id = str(existing.id)
            else:
                new_membership = UserMembership(
                    user_id=req.user_id,
                    tenant_id=req.tenant_id,
                    role_id=uuid.UUID(final_role_id),
                )
                session.add(new_membership)
                session.flush()
                membership_id = str(new_membership.id)

            req.status = "approved"
            req.requested_role_id = uuid.UUID(final_role_id)
            req.resolved_at = datetime.now(timezone.utc)
            if resolved_by:
                try:
                    req.resolved_by = uuid.UUID(resolved_by)
                except ValueError:
                    pass
            session.add(req)
            session.flush()

            return Ok({
                "request_id":    str(req.id),
                "status":        req.status,
                "membership_id": membership_id,
            })
        except Exception as e:
            logger.error(f"AccessRequestPostgresRepository.approve error: {e}")
            return Err(str(e))

    def reject(self, request_id: str, resolved_by: Optional[str], note: Optional[str]) -> Result[Dict[str, Any], str]:
        try:
            session = self.sql_session.session
            req = session.exec(
                select(AccessRequest).where(AccessRequest.id == uuid.UUID(request_id))
            ).first()
            if not req:
                return Err("REQUEST_NOT_FOUND")
            if req.status != "pending":
                return Err("REQUEST_ALREADY_RESOLVED")

            req.status = "rejected"
            req.resolved_at = datetime.now(timezone.utc)
            if note:
                req.note = note
            if resolved_by:
                try:
                    req.resolved_by = uuid.UUID(resolved_by)
                except ValueError:
                    pass
            session.add(req)
            session.flush()
            return Ok({"request_id": str(req.id), "status": req.status})
        except Exception as e:
            logger.error(f"AccessRequestPostgresRepository.reject error: {e}")
            return Err(str(e))
