import logging
import uuid
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.tenant_application_route_repository import TenantApplicationRouteRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import TenantApplicationRoute, TenantApplication

logger = logging.getLogger(__name__)


class TenantApplicationRoutePostgresRepository(TenantApplicationRouteRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self, tenant_application_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            stmt = select(TenantApplicationRoute)
            if tenant_application_id:
                stmt = stmt.where(
                    TenantApplicationRoute.tenant_application_id == uuid.UUID(tenant_application_id)
                )
            rows = self.sql_session.session.exec(stmt).all()
            return Ok([
                {
                    "id": str(r.id),
                    "tenant_application_id": str(r.tenant_application_id),
                    "host": r.host,
                    "path_prefix": r.path_prefix,
                    "is_default": r.is_default,
                    "is_active": r.is_active,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ])
        except Exception as e:
            logger.error(f"TenantApplicationRoutePostgresRepository.list_all error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            tenant_application_id = uuid.UUID(data["tenant_application_id"])
            tenant_app = self.sql_session.session.exec(
                select(TenantApplication).where(TenantApplication.id == tenant_application_id)
            ).first()
            if not tenant_app:
                return Err("TENANT_APPLICATION_NOT_FOUND")

            is_default = bool(data.get("is_default", False))
            if is_default:
                # Solo una ruta default por tenant-aplicación (índice único
                # parcial en BD) -- se desmarca cualquier default previo
                # dentro de la misma transacción para no chocar contra el
                # constraint ni dejar dos rutas default a medias.
                previous_default = self.sql_session.session.exec(
                    select(TenantApplicationRoute).where(
                        TenantApplicationRoute.tenant_application_id == tenant_application_id,
                        TenantApplicationRoute.is_default == True,  # noqa: E712
                    )
                ).first()
                if previous_default:
                    previous_default.is_default = False
                    self.sql_session.session.add(previous_default)
                    self.sql_session.session.flush()

            new_row = TenantApplicationRoute(
                tenant_application_id=tenant_application_id,
                host=data["host"],
                path_prefix=data.get("path_prefix") or "/",
                is_default=is_default,
            )
            self.sql_session.session.add(new_row)
            self.sql_session.session.flush()
            return Ok({
                "id": str(new_row.id),
                "tenant_application_id": str(new_row.tenant_application_id),
                "host": new_row.host,
                "path_prefix": new_row.path_prefix,
                "is_default": new_row.is_default,
                "is_active": new_row.is_active,
            })
        except Exception as e:
            logger.error(f"TenantApplicationRoutePostgresRepository.create error: {e}")
            return Err(str(e))

    def update(self, route_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(TenantApplicationRoute).where(TenantApplicationRoute.id == uuid.UUID(route_id))
            ).first()
            if not row:
                return Err("ROUTE_NOT_FOUND")

            if "host" in data and data["host"]:
                row.host = data["host"]
            if "path_prefix" in data and data["path_prefix"]:
                row.path_prefix = data["path_prefix"]
            if "is_default" in data and bool(data["is_default"]) and not row.is_default:
                previous_default = self.sql_session.session.exec(
                    select(TenantApplicationRoute).where(
                        TenantApplicationRoute.tenant_application_id == row.tenant_application_id,
                        TenantApplicationRoute.is_default == True,  # noqa: E712
                        TenantApplicationRoute.id != row.id,
                    )
                ).first()
                if previous_default:
                    previous_default.is_default = False
                    self.sql_session.session.add(previous_default)
                    self.sql_session.session.flush()
                row.is_default = True

            self.sql_session.session.add(row)
            self.sql_session.session.flush()
            return Ok({
                "id": str(row.id),
                "tenant_application_id": str(row.tenant_application_id),
                "host": row.host,
                "path_prefix": row.path_prefix,
                "is_default": row.is_default,
                "is_active": row.is_active,
            })
        except Exception as e:
            logger.error(f"TenantApplicationRoutePostgresRepository.update error: {e}")
            return Err(str(e))

    def toggle(self, route_id: str) -> Result[Dict[str, Any], str]:
        try:
            row = self.sql_session.session.exec(
                select(TenantApplicationRoute).where(TenantApplicationRoute.id == uuid.UUID(route_id))
            ).first()
            if not row:
                return Err("ROUTE_NOT_FOUND")
            row.is_active = not row.is_active
            self.sql_session.session.add(row)
            self.sql_session.session.flush()
            return Ok({"route_id": str(row.id), "is_active": row.is_active})
        except Exception as e:
            logger.error(f"TenantApplicationRoutePostgresRepository.toggle error: {e}")
            return Err(str(e))
