import logging
import uuid
import bcrypt
from datetime import datetime
from typing import Dict, Any, List
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.user_repository import UserRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import User

logger = logging.getLogger(__name__)


class UserPostgresRepository(UserRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        try:
            rows = self.sql_session.session.exec(
                select(User).order_by(User.full_name)
            ).all()
            users = [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "full_name": u.full_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in rows
            ]
            return Ok(users)
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
                role=data.get("role", "terapeuta"),
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
