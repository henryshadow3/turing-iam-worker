BEGIN;

CREATE SCHEMA IF NOT EXISTS turing;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE turing.tenants (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        varchar(50) UNIQUE NOT NULL,
    name        varchar(100) NOT NULL,
    redirect_url varchar(255) NOT NULL,
    is_active   bool DEFAULT true NOT NULL,
    created_at  timestamptz DEFAULT now() NOT NULL
);

CREATE TABLE turing.roles (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES turing.tenants(id) ON DELETE CASCADE,
    name        varchar(50) NOT NULL,
    is_active   bool DEFAULT true NOT NULL,
    created_at  timestamptz DEFAULT now() NOT NULL,
    UNIQUE(tenant_id, name)
);

CREATE TABLE turing.user_memberships (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
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
  ('951ed44f-2c83-4dfc-af59-0feb84beffff',
   'brilliant-therapy',
   'Brilliant Therapy',
   'http://localhost:3000/dashboard');

-- Seed: roles para brilliant-therapy
INSERT INTO turing.roles (id, tenant_id, name) VALUES
  ('98492cd2-d487-46aa-9e63-2f5063d9bf3a', '951ed44f-2c83-4dfc-af59-0feb84beffff', 'admin'),
  ('150a8019-9193-4b84-8994-bb6decae1ac1', '951ed44f-2c83-4dfc-af59-0feb84beffff', 'terapeuta'),
  ('69818f7d-9568-458e-b215-c8c9f0bbaf60', '951ed44f-2c83-4dfc-af59-0feb84beffff', 'padre'),
  ('db2fdc60-9516-41b4-9ed7-fc1e55100810', '951ed44f-2c83-4dfc-af59-0feb84beffff', 'alumno');

COMMIT;
