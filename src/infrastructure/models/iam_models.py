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
    # NULLABLE desde migración 017 (T-SP4-T2-I1 ADR 0001 §4): NULL para roles
    # de catálogo por aplicación (application_id NOT NULL en ese caso).
    # Filas legacy (rol organizacional de tenant, application_id NULL) siguen
    # con tenant_id poblado -- comportamiento intacto.
    tenant_id: Optional[uuid.UUID] = None
    name: str
    is_active: bool = Field(default=True)
    # NOT NULL en BD: sin default_factory SQLModel manda None explícito
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # NUEVO (migración 017): NOT NULL para roles de catálogo o custom por
    # tenant-app; NULL para el rol legacy organizacional (el que usa
    # user_memberships). Ver turing.roles_scope_chk.
    application_id: Optional[uuid.UUID] = None


class UserMembership(SQLModel, table=True):
    __tablename__ = "user_memberships"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role_id: uuid.UUID
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Application(SQLModel, table=True):
    """Catálogo de aplicaciones (turing.applications, migración 017).

    Entidad de primera clase sin tenant. IDs deterministas UUIDv5 (ADR 0001
    §6) sembrados por la migración -- este worker nunca genera un
    Application.id nuevo vía gen_random_uuid, solo lee/activa/desactiva el
    catálogo ya sembrado.
    """
    __tablename__ = "applications"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(primary_key=True)
    slug: str
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantApplication(SQLModel, table=True):
    """Habilitamiento de una Application para un Tenant (turing.tenant_applications).

    N:M resuelto entre Tenant y Application. Es la entidad a la que
    ApplicationMembership realmente apunta (nunca a Tenant o Application
    directamente).
    """
    __tablename__ = "tenant_applications"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID
    application_id: uuid.UUID
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApplicationMembership(SQLModel, table=True):
    """Acceso real de un usuario a una TenantApplication (turing.application_memberships).

    Es lo único que autoriza entrar a una aplicación (ADR 0001 §1 regla 2).
    NO confundir con UserMembership (afiliación pura al tenant, sin acceso).
    La BD exige (trigger enforce_membership_requires_affiliation, migración
    017) que exista una UserMembership activa al mismo tenant antes de
    insertar/actualizar una fila aquí -- este worker valida lo mismo en capa
    de aplicación antes de escribir (ver application_membership_create_action)
    para dar un mensaje de error claro en vez de depender solo de la
    excepción cruda del trigger.
    """
    __tablename__ = "application_memberships"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    tenant_application_id: uuid.UUID
    role_id: uuid.UUID
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantApplicationRoute(SQLModel, table=True):
    """Ruta (host + path) resuelta para una TenantApplication (turing.tenant_application_routes)."""
    __tablename__ = "tenant_application_routes"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_application_id: uuid.UUID
    host: str
    path_prefix: str = Field(default="/")
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MembershipSuspension(SQLModel, table=True):
    """Snapshot fila-por-fila de una suspensión global de membresía
    (turing.membership_suspensions, migración 019, W11 T-SP4-T2-I1).

    Registra qué filas de UserMembership/ApplicationMembership estaban
    is_active=true justo antes de un apagón global (iam.user.
    suspend_membership.in), para que la restauración
    (iam.user.restore_membership.in) reactive EXACTAMENTE esas filas y
    ninguna otra -- nunca una fila que ya estaba inactiva por otra razón
    antes del apagón. table_name/row_id son una referencia polimórfica
    (sin FK físico) a 'user_memberships' o 'application_memberships'.
    """
    __tablename__ = "membership_suspensions"
    __table_args__ = {"schema": "turing"}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    table_name: str
    row_id: uuid.UUID
    suspended_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    restored_at: Optional[datetime] = None
    is_active_suspension: bool = Field(default=True)


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
    # Aplicación que originó la solicitud (migración 031 de db-turing, B-SP8-7).
    # NULL en solicitudes previas o de clientes que no la envían: en ese caso
    # aprobar solo crea la afiliación al tenant (comportamiento histórico).
    application_id: Optional[uuid.UUID] = None
