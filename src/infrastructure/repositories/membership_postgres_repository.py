import logging
from typing import Dict, Any, List
from result import Result, Ok, Err

from domain.repositories.membership_repository import MembershipRepository
from infrastructure.database.session_manager import SQLSessionManager

logger = logging.getLogger(__name__)


class MembershipPostgresRepository(MembershipRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    um.id,
                    um.user_id,
                    u.email,
                    u.full_name,
                    um.tenant_id,
                    t.name  AS tenant_name,
                    um.role_id,
                    r.name  AS role_name,
                    um.is_active,
                    um.created_at
                FROM turing.user_memberships um
                JOIN brillaint_therapy.users u ON u.id = um.user_id
                JOIN turing.tenants          t ON t.id = um.tenant_id
                JOIN turing.roles            r ON r.id = um.role_id
                ORDER BY t.name, u.full_name
            """)
            rows = cur.fetchall()
            cur.close()
            memberships = [
                {
                    "id":          str(r[0]),
                    "user_id":     str(r[1]),
                    "email":       r[2],
                    "full_name":   r[3],
                    "tenant_id":   str(r[4]),
                    "tenant_name": r[5],
                    "role_id":     str(r[6]),
                    "role_name":   r[7],
                    "is_active":   r[8],
                    "created_at":  r[9].isoformat() if r[9] else None,
                }
                for r in rows
            ]
            return Ok(memberships)
        except Exception as e:
            logger.error(f"MembershipPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO turing.user_memberships (user_id, tenant_id, role_id)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, tenant_id, role_id
            """, (data["user_id"], data["tenant_id"], data["role_id"]))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return Ok({
                "id":        str(row[0]),
                "user_id":   str(row[1]),
                "tenant_id": str(row[2]),
                "role_id":   str(row[3]),
            })
        except Exception as e:
            conn.rollback()
            logger.error(f"MembershipPostgresRepository.create error: {e}")
            return Err(str(e))

    def delete(self, membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE turing.user_memberships
                SET is_active = false
                WHERE id = %s
                RETURNING id
            """, (membership_id,))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            if not row:
                return Err("MEMBERSHIP_NOT_FOUND")
            return Ok({"message": "ok", "membership_id": str(row[0])})
        except Exception as e:
            conn.rollback()
            logger.error(f"MembershipPostgresRepository.delete error: {e}")
            return Err(str(e))

    def update(self, membership_id: str, role_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE turing.user_memberships
                SET role_id = %s
                WHERE id = %s
                RETURNING id, user_id, tenant_id, role_id, is_active
            """, (role_id, membership_id))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            if not row:
                return Err("MEMBERSHIP_NOT_FOUND")
            return Ok({
                "id":        str(row[0]),
                "user_id":   str(row[1]),
                "tenant_id": str(row[2]),
                "role_id":   str(row[3]),
                "is_active": row[4],
            })
        except Exception as e:
            conn.rollback()
            logger.error(f"MembershipPostgresRepository.update error: {e}")
            return Err(str(e))

    def toggle(self, membership_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE turing.user_memberships
                SET is_active = NOT is_active
                WHERE id = %s
                RETURNING id, is_active
            """, (membership_id,))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            if not row:
                return Err("MEMBERSHIP_NOT_FOUND")
            return Ok({"membership_id": str(row[0]), "is_active": row[1]})
        except Exception as e:
            conn.rollback()
            logger.error(f"MembershipPostgresRepository.toggle error: {e}")
            return Err(str(e))
