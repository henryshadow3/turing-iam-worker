from dataclasses import dataclass
from typing import ClassVar
from domain.entities.tenant import Tenant


@dataclass(frozen=True)
class TenantCreated:
    tenant: Tenant

    EVENT_TYPE: ClassVar[str] = "iam.tenant.created"
    VERSION: ClassVar[int] = 1

    @classmethod
    def from_aggregate(cls, tenant: Tenant) -> "TenantCreated":
        return cls(tenant=tenant)

    def to_dict(self) -> dict:
        return {"tenant_id": self.tenant.id, "slug": self.tenant.slug, "name": self.tenant.name}
