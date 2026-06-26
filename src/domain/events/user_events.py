from dataclasses import dataclass
from typing import ClassVar
from domain.entities.user import User


@dataclass(frozen=True)
class UserCreated:
    user: User

    EVENT_TYPE: ClassVar[str] = "iam.user.created"
    VERSION: ClassVar[int] = 1

    @classmethod
    def from_aggregate(cls, user: User) -> "UserCreated":
        return cls(user=user)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user.id,
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
        }


@dataclass(frozen=True)
class UserUpdated:
    user: User

    EVENT_TYPE: ClassVar[str] = "iam.user.updated"
    VERSION: ClassVar[int] = 1

    @classmethod
    def from_aggregate(cls, user: User) -> "UserUpdated":
        return cls(user=user)

    def to_dict(self) -> dict:
        return {"user_id": self.user.id, "full_name": self.user.full_name, "role": self.user.role}


@dataclass(frozen=True)
class UserDisabled:
    user_id: str

    EVENT_TYPE: ClassVar[str] = "iam.user.disabled"
    VERSION: ClassVar[int] = 1

    def to_dict(self) -> dict:
        return {"user_id": self.user_id}
