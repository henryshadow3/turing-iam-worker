from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Optional
from datetime import datetime, timezone
import uuid


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str
    password_hash: str
    full_name: str
    role: str = Field(default="user")  # rol de PLATAFORMA (user/analista/developer/admin/superadmin)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email_verified: bool = Field(default=False)
    email_verification_code: Optional[str] = None
    email_verification_code_expires: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    reset_password_token: Optional[str] = None
    reset_password_expires: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    slug: str
    name: str
    redirect_url: str
    is_active: bool = Field(default=True)
    # NOT NULL en BD: sin default_factory SQLModel manda None explícito
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID
    name: str
    is_active: bool = Field(default=True)
    # NOT NULL en BD: sin default_factory SQLModel manda None explícito
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserMembership(SQLModel, table=True):
    __tablename__ = "user_memberships"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role_id: uuid.UUID
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccessRequest(SQLModel, table=True):
    __tablename__ = "access_requests"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    requested_role_id: Optional[uuid.UUID] = None
    status: str = Field(default="pending")  # pending | approved | rejected
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
