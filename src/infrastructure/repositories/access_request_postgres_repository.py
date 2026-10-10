import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import (
    AccessRequest, UserMembership, User, Tenant, Role,
    Application, TenantApplication, ApplicationMembership,
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
            app_ids    = list({r.application_id for r in requests if r.application_id})

            users   = {u.id: u for u in self.sql_session.session.exec(select(User).where(User.id.in_(user_ids))).all()} if user_ids else {}
            tenants = {t.id: t for t in self.sql_session.session.exec(select(Tenant).where(Tenant.id.in_(tenant_ids))).all()} if tenant_ids else {}
            roles   = {r.id: r for r in self.sql_session.session.exec(select(Role).where(Role.id.in_(role_ids))).all()} if role_ids else {}
            apps    = {a.id: a for a in self.sql_session.session.exec(select(Application).where(Application.id.in_(app_ids))).all()} if app_ids else {}

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
                    "application_id":    str(r.application_id) if r.application_id else None,
                    "application_slug":  apps[r.application_id].slug if r.application_id in apps else None,
                    "application_name":  apps[r.application_id].name if r.application_id in apps else None,
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

        B-SP8-7: si la solicitud trae application_id (la app que la originó,
        p. ej. bigminds), en la MISMA transacción se crea/reactiva además el
        acceso real a esa aplicación (turing.application_memberships), que es
        lo único que exige /auth/login. Si no se puede resolver (la app no
        está habilitada para el tenant, o no tiene un rol equivalente), la
        aprobación NO falla: queda solo la afiliación y la respuesta incluye
        application_access.granted=false con el motivo, para que el admin lo
        vea y lo resuelva desde Usuarios. Solicitudes sin application_id se
        comportan exactamente como antes.
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

            # El rol asignado debe existir, pertenecer al tenant de la solicitud
            # y estar activo (los roles desactivados no se pueden asignar).
            role = session.exec(
                select(Role).where(Role.id == uuid.UUID(final_role_id))
            ).first()
            if not role:
                return Err("ROLE_NOT_FOUND")
            if role.tenant_id != req.tenant_id:
                return Err("ROLE_TENANT_MISMATCH")
            if not role.is_active:
                return Err("ROLE_INACTIVE")

            # Resolución del acceso a la aplicación (solo lectura; TODA validación
            # va antes de cualquier escritura porque la sesión hace commit al
            # salir aunque el repo devuelva Err).
            app_plan = self._plan_application_access(req, role)

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

            # La afiliación debe estar flusheada antes: el trigger
            # enforce_membership_requires_affiliation la exige para insertar
            # el application_membership.
            session.flush()
            application_access = self._apply_application_access(req, app_plan)

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
                "application_id":   str(req.application_id) if req.application_id else None,
                "application_slug": app_plan.get("application_slug"),
                "application_access": application_access,
            })
        except Exception as e:
            logger.error(f"AccessRequestPostgresRepository.approve error: {e}")
            return Err(str(e))

    def _plan_application_access(self, req: AccessRequest, tenant_role: Role) -> Dict[str, Any]:
        """Decide (sin escribir) qué acceso de aplicación corresponde otorgar.

        Devuelve {"skip_reason": None|str, "application_slug", "tenant_application_id",
        "app_role_id"}. skip_reason != None significa que no se otorga acceso
        (no es un error: la afiliación igual se crea).

        Rol del acceso: el rol de TENANT elegido (legacy organizacional) no sirve
        para application_memberships cuando pertenece a otra aplicación; se usa el
        rol de CATÁLOGO de la aplicación con el mismo nombre (p. ej. tenant
        "padre" -> catálogo bigminds:padre). Si el rol elegido ya pertenece a la
        aplicación de la solicitud (rol custom por tenant-app), se usa tal cual.
        """
        if not req.application_id:
            return {"skip_reason": None, "application_slug": None}

        session = self.sql_session.session
        app_row = session.exec(
            select(Application).where(Application.id == req.application_id)
        ).first()
        if not app_row:
            return {"skip_reason": "APPLICATION_NOT_FOUND", "application_slug": None}
        plan: Dict[str, Any] = {"skip_reason": None, "application_slug": app_row.slug}
        if not app_row.is_active:
            plan["skip_reason"] = "APPLICATION_INACTIVE"
            return plan

        tenant_app = session.exec(
            select(TenantApplication).where(
                TenantApplication.tenant_id == req.tenant_id,
                TenantApplication.application_id == req.application_id,
            )
        ).first()
        if not tenant_app:
            plan["skip_reason"] = "APPLICATION_NOT_ENABLED_FOR_TENANT"
            return plan
        if not tenant_app.is_active:
            plan["skip_reason"] = "TENANT_APPLICATION_INACTIVE"
            return plan
        plan["tenant_application_id"] = tenant_app.id

        if tenant_role.application_id == req.application_id:
            app_role = tenant_role
        else:
            app_role = session.exec(
                select(Role).where(
                    Role.application_id == req.application_id,
                    Role.tenant_id.is_(None),
                    Role.name == tenant_role.name,
                    Role.is_active == True,  # noqa: E712
                )
            ).first()
        if not app_role or not app_role.is_active:
            plan["skip_reason"] = "APPLICATION_ROLE_NOT_FOUND"
            return plan
        plan["app_role_id"] = app_role.id
        return plan

    def _apply_application_access(self, req: AccessRequest, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ejecuta el plan: crea o reactiva el application_membership (UNIQUE
        user + tenant_application, igual que la afiliación). None si la
        solicitud no traía aplicación."""
        if not req.application_id:
            return None
        if plan.get("skip_reason"):
            logger.warning(
                f"Aprobación {req.id}: acceso a aplicación {req.application_id} no otorgado "
                f"({plan['skip_reason']}); solo afiliación al tenant."
            )
            return {"granted": False, "reason": plan["skip_reason"]}

        session = self.sql_session.session
        existing = session.exec(
            select(ApplicationMembership).where(
                ApplicationMembership.user_id == req.user_id,
                ApplicationMembership.tenant_application_id == plan["tenant_application_id"],
            )
        ).first()
        if existing:
            existing.role_id = plan["app_role_id"]
            existing.is_active = True
            session.add(existing)
            row = existing
        else:
            row = ApplicationMembership(
                user_id=req.user_id,
                tenant_application_id=plan["tenant_application_id"],
                role_id=plan["app_role_id"],
            )
            session.add(row)
        session.flush()
        return {
            "granted": True,
            "reason": None,
            "application_membership_id": str(row.id),
            "role_id": str(plan["app_role_id"]),
        }

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
