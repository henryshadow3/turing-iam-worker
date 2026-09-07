import logging
import uuid
import bcrypt
from datetime import datetime
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select, func
from sqlalchemy import or_, and_

from domain.repositories.user_repository import UserRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import (
    User,
    UserMembership,
    ApplicationMembership,
    TenantApplication,
)

logger = logging.getLogger(__name__)

# Límite superior defensivo para "limit" -- evita que un caller sin querer
# (o malicioso) pida una página del tamaño de toda la tabla, que es
# exactamente el problema de escala que esta paginación server-side viene a
# resolver (ver Work Item T-SP4-T2-I1-W7, requisito de Henry).
MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50


class UserPostgresRepository(UserRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    @staticmethod
    def _serialize(u: User) -> Dict[str, Any]:
        return {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }

    def list_all(
        self,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        application_id: Optional[str] = None,
        app_access_status: Optional[str] = None,
    ) -> Result[Dict[str, Any], str]:
        """Lista usuarios con filtros y paginación OPCIONALES, resueltos en
        SQL (server-side) para escalar a miles de filas -- ninguno de los
        parámetros es requerido, así que cualquier llamador preexistente que
        invoque list_all() sin argumentos sigue funcionando exactamente
        igual que antes (mismo orden, mismas filas), solo que ahora la
        respuesta también trae "total" (aditivo, ver user_list_action).

        No se pagina por defecto en el sentido de "cortar filas" salvo que
        el caller pase limit/offset explícitamente -- así ningún consumidor
        actual (que no sabe de estos parámetros) ve un comportamiento
        distinto al de antes de este Work Item.

        `application_id` (T-SP4-T2-I1-W12, aditivo): filtra server-side a
        los usuarios "relevantes" para una aplicación del catálogo -- unión
        de dos grupos, para alimentar las tabs por aplicación de Users.jsx
        sin traer TODOS los usuarios al cliente (misma lección de escala de
        W7):
          (a) usuarios con al menos un ApplicationMembership (activo o no)
              cuya tenant_application apunta a esa aplicación.
          (b) usuarios "afiliados sin acceso": tienen una UserMembership
              ACTIVA a un tenant donde esa aplicación está habilitada
              (tenant_applications.is_active=true), pero SIN ningún
              ApplicationMembership para esa combinación tenant+app.
        Cada fila devuelta trae "app_access_status": "access" | "affiliated_no_access"
        cuando application_id está presente (None en cualquier otro caso).
        `app_access_status` opcional adicional filtra al subconjunto (a) o
        (b) exclusivamente -- usado por la búsqueda/paginación dentro de una
        tab para no mezclar ambos grupos en una sola página cortada a la
        mitad (ver Users.jsx: cada grupo se pagina por separado).
        """
        try:
            app_uuid = uuid.UUID(application_id) if application_id else None

            # Subquery: user_ids con AL MENOS un application_membership para
            # esta aplicación (grupo "access"). No filtra por is_active del
            # access -- el toggle por-app opera igual sobre usuarios con
            # accesos actualmente desactivados (siguen siendo del grupo "a",
            # el toggle real les aplica).
            access_user_ids_subq = None
            affiliated_user_ids_subq = None
            if app_uuid is not None:
                access_user_ids_subq = (
                    select(ApplicationMembership.user_id)
                    .join(
                        TenantApplication,
                        TenantApplication.id == ApplicationMembership.tenant_application_id,
                    )
                    .where(TenantApplication.application_id == app_uuid)
                    .distinct()
                )
                # Subquery: user_ids afiliados (UserMembership activa) a un
                # tenant que tiene esta app habilitada, EXCLUYENDO a los que
                # ya están en el grupo "access" (evita que un usuario
                # aparezca duplicado entre grupos por otro tenant).
                affiliated_tenant_ids_subq = (
                    select(TenantApplication.tenant_id)
                    .where(
                        TenantApplication.application_id == app_uuid,
                        TenantApplication.is_active == True,  # noqa: E712
                    )
                )
                affiliated_user_ids_subq = (
                    select(UserMembership.user_id)
                    .where(
                        UserMembership.tenant_id.in_(affiliated_tenant_ids_subq),
                        UserMembership.is_active == True,  # noqa: E712
                    )
                    .where(UserMembership.user_id.not_in(access_user_ids_subq))
                    .distinct()
                )

            stmt = select(User)
            count_stmt = select(func.count()).select_from(User)

            if search:
                like = f"%{search.strip().lower()}%"
                condition = or_(
                    func.lower(User.full_name).like(like),
                    func.lower(User.email).like(like),
                )
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

            if role:
                stmt = stmt.where(User.role == role)
                count_stmt = count_stmt.where(User.role == role)

            if is_active is not None:
                stmt = stmt.where(User.is_active == is_active)
                count_stmt = count_stmt.where(User.is_active == is_active)

            if app_uuid is not None:
                if app_access_status == "access":
                    condition = User.id.in_(access_user_ids_subq)
                elif app_access_status == "affiliated_no_access":
                    condition = User.id.in_(affiliated_user_ids_subq)
                else:
                    condition = or_(
                        User.id.in_(access_user_ids_subq),
                        User.id.in_(affiliated_user_ids_subq),
                    )
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

            total = self.sql_session.session.exec(count_stmt).one()

            stmt = stmt.order_by(User.full_name)

            # Paginación real: solo se aplica si el caller pidió limit
            # explícitamente (comportamiento aditivo, ver docstring).
            if limit is not None:
                safe_limit = max(1, min(int(limit), MAX_PAGE_SIZE))
                stmt = stmt.limit(safe_limit)
                if offset is not None:
                    stmt = stmt.offset(max(0, int(offset)))

            rows = self.sql_session.session.exec(stmt).all()

            # Anota app_access_status por usuario cuando se filtró por app --
            # una sola query extra sobre el subconjunto ya paginado (nunca
            # sobre la tabla completa), consistente con el resto del método.
            access_status_by_user: Dict[uuid.UUID, str] = {}
            if app_uuid is not None and rows:
                row_ids = [u.id for u in rows]
                access_ids = set(self.sql_session.session.exec(
                    select(ApplicationMembership.user_id)
                    .join(
                        TenantApplication,
                        TenantApplication.id == ApplicationMembership.tenant_application_id,
                    )
                    .where(
                        TenantApplication.application_id == app_uuid,
                        ApplicationMembership.user_id.in_(row_ids),
                    )
                    .distinct()
                ).all())
                for uid in row_ids:
                    access_status_by_user[uid] = "access" if uid in access_ids else "affiliated_no_access"

            users = []
            for u in rows:
                serialized = self._serialize(u)
                if app_uuid is not None:
                    serialized["app_access_status"] = access_status_by_user.get(u.id)
                users.append(serialized)

            return Ok({"users": users, "total": total})
        except Exception as e:
            logger.error(f"UserPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, user_id: str) -> Result[Dict[str, Any], str]:
        try:
            user = self.sql_session.session.exec(
                select(User).where(User.id == uuid.UUID(user_id))
            ).first()
            if not user:
                return Err("USER_NOT_FOUND")
            return Ok({
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        except Exception as e:
            logger.error(f"UserPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            hashed = bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            new_user = User(
                email=data["email"],
                password_hash=hashed,
                full_name=data["full_name"],
                role=data.get("role", "user"),
                is_active=True,
            )
            self.sql_session.session.add(new_user)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_user.id),
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
            })
        except Exception as e:
            logger.error(f"UserPostgresRepository.create error: {e}")
            return Err(str(e))

    def update(self, user_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            user = self.sql_session.session.exec(
                select(User).where(User.id == uuid.UUID(user_id))
            ).first()
            if not user:
                return Err("USER_NOT_FOUND")
            if data.get("full_name"):
                user.full_name = data["full_name"]
            if data.get("role"):
                user.role = data["role"]
            if data.get("is_active") is not None:
                user.is_active = data["is_active"]
            user.updated_at = datetime.utcnow()
            self.sql_session.session.add(user)
            self.sql_session.session.flush()
            return Ok({
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
            })
        except Exception as e:
            logger.error(f"UserPostgresRepository.update error: {e}")
            return Err(str(e))

    def disable(self, user_id: str) -> Result[Dict[str, Any], str]:
        try:
            user = self.sql_session.session.exec(
                select(User).where(User.id == uuid.UUID(user_id))
            ).first()
            if not user:
                return Err("USER_NOT_FOUND")
            user.is_active = False
            user.updated_at = datetime.utcnow()
            self.sql_session.session.add(user)
            self.sql_session.session.flush()
            return Ok({"message": "ok", "user_id": str(user.id)})
        except Exception as e:
            logger.error(f"UserPostgresRepository.disable error: {e}")
            return Err(str(e))
