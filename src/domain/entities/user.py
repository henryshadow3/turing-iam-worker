from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class User:
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(email: str, full_name: str, role: str = "terapeuta") -> "User":
        return User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=full_name,
            role=role,
            is_active=True,
        )
