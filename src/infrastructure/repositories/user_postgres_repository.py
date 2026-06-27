import logging
import uuid
import bcrypt
from typing import Dict, Any, List
from result import Result, Ok, Err

from domain.repositories.user_repository import UserRepository
from infrastructure.database.session_manager import SQLSessionManager

logger = logging.getLogger(__name__)


class UserPostgresRepository(UserRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, full_name, role, is_active, created_at
                FROM brillaint_therapy.users
                ORDER BY full_name
            """)
            rows = cur.fetchall()
            cur.close()
            users = [
                {
                    "id": str(r[0]),
                    "email": r[1],
                    "full_name": r[2],
                    "role": r[3],
                    "is_active": r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ]
            return Ok(users)
        except Exception as e:
            logger.error(f"UserPostgresRepository.list_all error: {e}")
            return Err(str(e))

    def get_by_id(self, user_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, full_name, role, is_active, created_at
                FROM brillaint_therapy.users
                WHERE id = %s
            """, (user_id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return Err("USER_NOT_FOUND")
            return Ok({
                "id": str(row[0]),
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "is_active": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            })
        except Exception as e:
            logger.error(f"UserPostgresRepository.get_by_id error: {e}")
            return Err(str(e))

    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            hashed = bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO brillaint_therapy.users
                    (email, password_hash, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, true)
                RETURNING id, email, full_name, role
            """, (
                data["email"],
                hashed,
                data["full_name"],
                data.get("role", "terapeuta"),
            ))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return Ok({"id": str(row[0]), "email": row[1], "full_name": row[2], "role": row[3]})
        except Exception as e:
            conn.rollback()
            logger.error(f"UserPostgresRepository.create error: {e}")
            return Err(str(e))

    def update(self, user_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            is_active = data.get("is_active")
            cur.execute("""
                UPDATE brillaint_therapy.users
                SET full_name  = COALESCE(%s, full_name),
                    role       = COALESCE(%s, role),
                    is_active  = CASE WHEN %s IS NOT NULL THEN %s ELSE is_active END,
                    updated_at = now()
                WHERE id = %s
                RETURNING id, email, full_name, role, is_active
            """, (data.get("full_name"), data.get("role"), is_active, is_active, user_id))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            if not row:
                return Err("USER_NOT_FOUND")
            return Ok({"id": str(row[0]), "email": row[1], "full_name": row[2], "role": row[3], "is_active": row[4]})
        except Exception as e:
            conn.rollback()
            logger.error(f"UserPostgresRepository.update error: {e}")
            return Err(str(e))

    def disable(self, user_id: str) -> Result[Dict[str, Any], str]:
        try:
            conn = self.sql_session.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE brillaint_therapy.users
                SET is_active = false, updated_at = now()
                WHERE id = %s
                RETURNING id
            """, (user_id,))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            if not row:
                return Err("USER_NOT_FOUND")
            return Ok({"message": "ok", "user_id": str(row[0])})
        except Exception as e:
            conn.rollback()
            logger.error(f"UserPostgresRepository.disable error: {e}")
            return Err(str(e))
