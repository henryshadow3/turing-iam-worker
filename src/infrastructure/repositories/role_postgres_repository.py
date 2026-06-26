import logging
from typing import Dict, Any, List, Optional
from result import Result, Ok, Err

from domain.repositories.role_repository import RoleRepository
from infrastructure.database.session_manager import SQLSessionManager

logger = logging.getLogger(__name__)


class RolePostgresRepository(RoleRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_by_tenant(self, tenant_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            if tenant_id:
                cur.execute("""
                    SELECT r.id, r.tenant_id, r.name, r.is_active, t.name as tenant_name
                    FROM turing.roles r
                    JOIN turing.tenants t ON t.id = r.tenant_id
                    WHERE r.tenant_id = %s
                    ORDER BY r.name
                """, (tenant_id,))
            else:
                cur.execute("""
                    SELECT r.id, r.tenant_id, r.name, r.is_active, t.name as tenant_name
                    FROM turing.roles r
                    JOIN turing.tenants t ON t.id = r.tenant_id
                    ORDER BY t.name, r.name
                """)
            rows = cur.fetchall()
            cur.close()
            roles = [
                {
                    "id": str(r[0]),
                    "tenant_id": str(r[1]),
                    "name": r[2],
                    "is_active": r[3],
                    "tenant_name": r[4],
                }
                for r in rows
            ]
            return Ok(roles)
        except Exception as e:
            logger.error(f"RolePostgresRepository.list_by_tenant error: {e}")
            return Err(str(e))

    def get_by_id(self, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, tenant_id, name, is_active
                FROM turing.roles WHERE id = %s
            """, (role_id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return Err("ROLE_NOT_FOUND")
            return Ok({"id": str(row[0]), "tenant_id": str(row[1]), "name": row[2], "is_active": row[3]})
        except Exception as e:
            logger.error(f"RolePostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO turing.roles (tenant_id, name)
                VALUES (%s, %s)
                RETURNING id, tenant_id, name
            """, (data["tenant_id"], data["name"]))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return Ok({"id": str(row[0]), "tenant_id": str(row[1]), "name": row[2]})
        except Exception as e:
            conn.rollback()
            logger.error(f"RolePostgresRepository.create error: {e}")
            return Err(str(e))
