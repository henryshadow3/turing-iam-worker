from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Role:
    id: str
    tenant_id: str
    name: str
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(tenant_id: str, name: str) -> "Role":
        return Role(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            is_active=True,
        )
