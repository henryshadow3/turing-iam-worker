from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from typing import Optional
from datetime import datetime
import uuid


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"schema": "brillaint_therapy"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str
    password_hash: str
    full_name: str
    role: str = Field(default="terapeuta")
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
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
    created_at: Optional[datetime] = None


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID
    name: str
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None


class UserMembership(SQLModel, table=True):
    __tablename__ = "user_memberships"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role_id: uuid.UUID
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
