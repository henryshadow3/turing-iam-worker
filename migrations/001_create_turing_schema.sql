BEGIN;

CREATE SCHEMA IF NOT EXISTS turing;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE turing.tenants (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug        varchar(50) UNIQUE NOT NULL,
    name        varchar(100) NOT NULL,
    redirect_url varchar(255) NOT NULL,
    is_active   bool DEFAULT true NOT NULL,
    created_at  timestamptz DEFAULT now() NOT NULL
);

CREATE TABLE turing.roles (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id   uuid NOT NULL REFERENCES turing.tenants(id) ON DELETE CASCADE,
    name        varchar(50) NOT NULL,
    is_active   bool DEFAULT true NOT NULL,
    created_at  timestamptz DEFAULT now() NOT NULL,
    UNIQUE(tenant_id, name)
);

CREATE TABLE turing.user_memberships (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     uuid NOT NULL REFERENCES brillaint_therapy.users(id) ON DELETE CASCADE,
    tenant_id   uuid NOT NULL REFERENCES turing.tenants(id) ON DELETE CASCADE,
    role_id     uuid NOT NULL REFERENCES turing.roles(id) ON DELETE CASCADE,
    is_active   bool DEFAULT true NOT NULL,
    created_at  timestamptz DEFAULT now() NOT NULL,
    UNIQUE(user_id, tenant_id)
);

CREATE INDEX idx_memberships_user   ON turing.user_memberships(user_id);
CREATE INDEX idx_memberships_tenant ON turing.user_memberships(tenant_id);
CREATE INDEX idx_roles_tenant       ON turing.roles(tenant_id);

-- Seed: tenant brilliant-therapy
INSERT INTO turing.tenants (id, slug, name, redirect_url) VALUES
  ('00000000-0000-0000-0000-000000000001',
   'brilliant-therapy',
   'Brilliant Therapy',
   'http://localhost:3001/dashboard');

-- Seed: roles para brilliant-therapy
INSERT INTO turing.roles (id, tenant_id, name) VALUES
  ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'admin'),
  ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'terapeuta'),
  ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'padre'),
  ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000001', 'alumno');

COMMIT;
