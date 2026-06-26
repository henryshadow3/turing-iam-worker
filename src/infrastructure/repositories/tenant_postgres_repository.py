import logging
from typing import Dict, Any, List
from result import Result, Ok, Err

from domain.repositories.tenant_repository import TenantRepository
from infrastructure.database.session_manager import SQLSessionManager

logger = logging.getLogger(__name__)


class TenantPostgresRepository(TenantRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, slug, name, redirect_url, is_active, created_at
                FROM turing.tenants
                ORDER BY name
            """)
            rows = cur.fetchall()
            cur.close()
            tenants = [
                {
                    "id": str(r[0]),
                    "slug": r[1],
                    "name": r[2],
                    "redirect_url": r[3],
                    "is_active": r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ]
            return Ok(tenants)
        except Exception as e:
            logger.error(f"TenantPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, tenant_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, slug, name, redirect_url, is_active
                FROM turing.tenants
                WHERE id = %s
            """, (tenant_id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return Err("TENANT_NOT_FOUND")
            return Ok({"id": str(row[0]), "slug": row[1], "name": row[2], "redirect_url": row[3], "is_active": row[4]})
        except Exception as e:
            logger.error(f"TenantPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO turing.tenants (slug, name, redirect_url)
                VALUES (%s, %s, %s)
                RETURNING id, slug, name, redirect_url
            """, (data["slug"], data["name"], data["redirect_url"]))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return Ok({"id": str(row[0]), "slug": row[1], "name": row[2], "redirect_url": row[3]})
        except Exception as e:
            conn.rollback()
            logger.error(f"TenantPostgresRepository.create error: {e}")
            return Err(str(e))
