from dataclasses import dataclass
from typing import ClassVar
from domain.entities.membership import Membership


@dataclass(frozen=True)
class MembershipCreated:
    membership: Membership

    EVENT_TYPE: ClassVar[str] = "iam.membership.created"
    VERSION: ClassVar[int] = 1

    @classmethod
    def from_aggregate(cls, membership: Membership) -> "MembershipCreated":
        return cls(membership=membership)

    def to_dict(self) -> dict:
        return {
            "membership_id": self.membership.id,
            "user_id": self.membership.user_id,
            "tenant_id": self.membership.tenant_id,
            "role_id": self.membership.role_id,
        }


@dataclass(frozen=True)
class MembershipDeleted:
    membership_id: str

    EVENT_TYPE: ClassVar[str] = "iam.membership.deleted"
    VERSION: ClassVar[int] = 1

    def to_dict(self) -> dict:
        return {"membership_id": self.membership_id}
