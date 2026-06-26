from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Membership:
    id: str
    user_id: str
    tenant_id: str
    role_id: str
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(user_id: str, tenant_id: str, role_id: str) -> "Membership":
        return Membership(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            role_id=role_id,
            is_active=True,
        )
