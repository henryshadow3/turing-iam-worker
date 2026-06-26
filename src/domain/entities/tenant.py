from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Tenant:
    id: str
    slug: str
    name: str
    redirect_url: str
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(slug: str, name: str, redirect_url: str) -> "Tenant":
        return Tenant(
            id=str(uuid.uuid4()),
            slug=slug,
            name=name,
            redirect_url=redirect_url,
            is_active=True,
        )
