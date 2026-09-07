import logging
import uuid
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.application_membership_repository import ApplicationMembershipRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import (
    ApplicationMembership,
    TenantApplication,
    UserMembership,
    User,
    Tenant,
    Application,
    Role,
)

logger = logging.getLogger(__name__)


class ApplicationMembershipPostgresRepository(ApplicationMembershipRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def _enrich(self, rows: List[ApplicationMembership]) -> List[Dict[str, Any]]:
        user_ids = list({r.user_id for r in rows})
        tapp_ids = list({r.tenant_application_id for r in rows})
        role_ids = list({r.role_id for r in rows})

        users = {u.id: u for u in self.sql_session.session.exec(
            select(User).where(User.id.in_(user_ids))
        ).all()} if user_ids else {}
        tapps = {t.id: t for t in self.sql_session.session.exec(
            select(TenantApplication).where(TenantApplication.id.in_(tapp_ids))
        ).all()} if tapp_ids else {}
        roles = {r.id: r for r in self.sql_session.session.exec(
            select(Role).where(Role.id.in_(role_ids))
        ).all()} if role_ids else {}

        tenant_ids = list({t.tenant_id for t in tapps.values()})
        app_ids    = list({t.application_id for t in tapps.values()})
        tenants = {t.id: t for t in self.sql_session.session.exec(
            select(Tenant).where(Tenant.id.in_(tenant_ids))
        ).all()} if tenant_ids else {}
        apps = {a.id: a for a in self.sql_session.session.exec(
            select(Application).where(Application.id.in_(app_ids))
        ).all()} if app_ids else {}

        result = []
        for r in rows:
            tapp = tapps.get(r.tenant_application_id)
            tenant = tenants.get(tapp.tenant_id) if tapp else None
            application = apps.get(tapp.application_id) if tapp else None
            result.append({
                "id": str(r.id),
                "user_id": str(r.user_id),
                "email": users[r.user_id].email if r.user_id in users else None,
                "tenant_application_id": str(r.tenant_application_id),
                "tenant_id": str(tenant.id) if tenant else None,
                "tenant_slug": tenant.slug if tenant else None,
                "application_id": str(application.id) if application else None,
                "application_slug": application.slug if application else None,
                "role_id": str(r.role_id),
                "role_name": roles[r.role_id].name if r.role_id in roles else None,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return result

    def list_all(self, user_id: Optional[str] = None,
                 tenant_application_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            stmt = select(ApplicationMembership)
            if user_id:
                stmt = stmt.where(ApplicationMembership.user_id == uuid.UUID(user_id))
            if tenant_application_id:
                stmt = stmt.where(
                    ApplicationMembership.tenant_application_id == uuid.UUID(tenant_application_id)
                )
            rows = self.sql_session.session.exec(stmt).all()
            return Ok(self._enrich(rows))
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, application_membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(ApplicationMembership).where(
                    ApplicationMembership.id == uuid.UUID(application_membership_id)
                )
            ).first()
            if not row:
                return Err("APPLICATION_MEMBERSHIP_NOT_FOUND")
            enriched = self._enrich([row])
            return Ok(enriched[0])
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        """Crea el acceso real a una tenant-aplicación.

        Regla dura (ADR 0001 §1 regla 4 / Work Item W5): exige que exista una
        UserMembership ACTIVA del mismo usuario al tenant dueño de la
        tenant_application indicada. Se valida aquí, en capa de aplicación,
        ANTES de intentar el INSERT -- el trigger de BD
        (enforce_membership_requires_affiliation, migración 017) es la última
        línea de defensa, pero queremos un Err(...) legible en vez de
        depender de que la excepción cruda del trigger burbujee como
        IntegrityError genérico.
        """
        try:
            user_id = uuid.UUID(data["user_id"])
            tenant_application_id = uuid.UUID(data["tenant_application_id"])
            role_id = uuid.UUID(data["role_id"])

            user = self.sql_session.session.exec(
                select(User).where(User.id == user_id)
            ).first()
            if not user:
                return Err("USER_NOT_FOUND")

            tenant_app = self.sql_session.session.exec(
                select(TenantApplication).where(TenantApplication.id == tenant_application_id)
            ).first()
            if not tenant_app:
                return Err("TENANT_APPLICATION_NOT_FOUND")
            if not tenant_app.is_active:
                return Err("TENANT_APPLICATION_INACTIVE")

            role = self.sql_session.session.exec(
                select(Role).where(Role.id == role_id)
            ).first()
            if not role:
                return Err("ROLE_NOT_FOUND")
            if not role.is_active:
                return Err("ROLE_INACTIVE")
            # El rol debe pertenecer a la misma aplicación que la
            # tenant_application (catálogo: role.tenant_id IS NULL; custom:
            # role.tenant_id == tenant_app.tenant_id) — mismo espíritu que
            # membership_create_action valida ROLE_TENANT_MISMATCH.
            if role.application_id != tenant_app.application_id:
                return Err("ROLE_APPLICATION_MISMATCH")
            if role.tenant_id is not None and role.tenant_id != tenant_app.tenant_id:
                return Err("ROLE_TENANT_MISMATCH")

            # Regla dura: afiliación activa previa al tenant dueño de la app.
            affiliated = self.sql_session.session.exec(
                select(UserMembership).where(
                    UserMembership.user_id == user_id,
                    UserMembership.tenant_id == tenant_app.tenant_id,
                    UserMembership.is_active == True,  # noqa: E712
                )
            ).first()
            if not affiliated:
                return Err("USER_NOT_AFFILIATED_TO_TENANT")

            existing = self.sql_session.session.exec(
                select(ApplicationMembership).where(
                    ApplicationMembership.user_id == user_id,
                    ApplicationMembership.tenant_application_id == tenant_application_id,
                )
            ).first()
            if existing:
                return Err("APPLICATION_MEMBERSHIP_ALREADY_EXISTS")

            new_row = ApplicationMembership(
                user_id=user_id,
                tenant_application_id=tenant_application_id,
                role_id=role_id,
            )
            self.sql_session.session.add(new_row)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_row.id),
                "user_id": str(new_row.user_id),
                "tenant_application_id": str(new_row.tenant_application_id),
                "role_id": str(new_row.role_id),
                "is_active": new_row.is_active,
            })
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.create error: {e}")
            return Err(str(e))

    def update(self, application_membership_id: str, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(ApplicationMembership).where(
                    ApplicationMembership.id == uuid.UUID(application_membership_id)
                )
            ).first()
            if not row:
                return Err("APPLICATION_MEMBERSHIP_NOT_FOUND")

            new_role_id = uuid.UUID(role_id)
            role = self.sql_session.session.exec(
                select(Role).where(Role.id == new_role_id)
            ).first()
            if not role:
                return Err("ROLE_NOT_FOUND")
            if not role.is_active:
                return Err("ROLE_INACTIVE")

            tenant_app = self.sql_session.session.exec(
                select(TenantApplication).where(TenantApplication.id == row.tenant_application_id)
            ).first()
            if not tenant_app:
                return Err("TENANT_APPLICATION_NOT_FOUND")
            if role.application_id != tenant_app.application_id:
                return Err("ROLE_APPLICATION_MISMATCH")
            if role.tenant_id is not None and role.tenant_id != tenant_app.tenant_id:
                return Err("ROLE_TENANT_MISMATCH")

            row.role_id = new_role_id
            self.sql_session.session.add(row)
            self.sql_session.session.flush()
            return Ok({
                "id": str(row.id),
                "user_id": str(row.user_id),
                "tenant_application_id": str(row.tenant_application_id),
                "role_id": str(row.role_id),
                "is_active": row.is_active,
            })
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.update error: {e}")
            return Err(str(e))

    def toggle(self, application_membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(ApplicationMembership).where(
                    ApplicationMembership.id == uuid.UUID(application_membership_id)
                )
            ).first()
            if not row:
                return Err("APPLICATION_MEMBERSHIP_NOT_FOUND")
            row.is_active = not row.is_active
            self.sql_session.session.add(row)
            self.sql_session.session.flush()
            return Ok({"application_membership_id": str(row.id), "is_active": row.is_active})
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.toggle error: {e}")
            return Err(str(e))

    def toggle_by_application(self, user_id: str, application_id: str) -> Result[Dict[str, Any], str]:
        """iam.user.toggle_application_access.in (T-SP4-T2-I1-W12) -- alterna
        de UN JALÓN, en una sola transacción, TODOS los ApplicationMembership
        de un usuario para una aplicación (cruzando TODOS los tenants donde
        tiene acceso a esa app, vía tenant_applications.application_id) --
        no un tenant a la vez.

        Semántica del toggle (decidida por ser la más simple y predecible,
        ver test report): si el usuario tiene AL MENOS UN acceso activo a
        esta app, el toggle DESACTIVA todos. Si no tiene ninguno activo
        (todos inactivos, o no tiene ninguna fila), el toggle ACTIVA todas
        las filas EXISTENTES (nunca crea accesos nuevos -- esto solo
        prende/apaga accesos que ya existen, otorgar un acceso nuevo sigue
        siendo iam.application_membership.create.in).

        Sin snapshot (a diferencia de MembershipSuspensionPostgresRepository
        de W11): ahí hacía falta snapshot porque la restauración debe
        reactivar EXACTAMENTE las filas que estaban activas antes de un
        apagón que también toca user_memberships (afectando dos tablas con
        semántica de restauración exacta). Aquí el toggle es de una sola
        tabla, con un estado binario efectivo claro (¿hay algo activo o
        no?) -- guardar snapshot añadiría complejidad sin un caso de uso
        real que lo requiera (revertir un toggle por-app simplemente es
        volver a darle clic al mismo botón, que ya invierte el estado
        correctamente sin snapshot).
        """
        try:
            uid = uuid.UUID(user_id)
            app_uuid = uuid.UUID(application_id)

            rows = self.sql_session.session.exec(
                select(ApplicationMembership)
                .join(
                    TenantApplication,
                    TenantApplication.id == ApplicationMembership.tenant_application_id,
                )
                .where(
                    ApplicationMembership.user_id == uid,
                    TenantApplication.application_id == app_uuid,
                )
            ).all()

            if not rows:
                return Err("NO_APPLICATION_ACCESS_FOR_USER")

            any_active = any(r.is_active for r in rows)
            new_state = not any_active

            for row in rows:
                row.is_active = new_state
                self.sql_session.session.add(row)

            self.sql_session.session.flush()
            return Ok({
                "user_id": str(uid),
                "application_id": str(app_uuid),
                "is_active": new_state,
                "affected_count": len(rows),
            })
        except Exception as e:
            logger.error(f"ApplicationMembershipPostgresRepository.toggle_by_application error: {e}")
            return Err(str(e))
