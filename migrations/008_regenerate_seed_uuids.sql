-- 008_regenerate_seed_uuids.sql
--
-- Reemplaza los UUIDs seed "falsos" (00000000-...) del tenant brilliant-therapy
-- y sus 4 roles por UUIDs aleatorios reales, actualizando en cascada todas las
-- tablas que los referencian.
--
-- IMPORTANTE (orden en producción): ejecutar DESPUÉS de la 003 y ANTES de la
-- 004 — la 004 backfillea tenant_id en las tablas de negocio usando ya el UUID
-- nuevo. Las FKs de esas tablas (students/planning_registry/activity_catalog)
-- y la de access_requests pueden no existir aún en ese punto; por eso todos los
-- DROP CONSTRAINT usan IF EXISTS y solo se recrean las que existían.
--
-- Idempotente: si los UUIDs viejos ya no existen (p.ej. en local, donde este
-- cambio se aplicó a mano), todos los UPDATE son no-op.

BEGIN;

-- ── 1. Soltar FKs que referencian turing.tenants y turing.roles ──────────────
ALTER TABLE turing.roles              DROP CONSTRAINT IF EXISTS roles_tenant_id_fkey;
ALTER TABLE turing.user_memberships   DROP CONSTRAINT IF EXISTS user_memberships_tenant_id_fkey;
ALTER TABLE turing.user_memberships   DROP CONSTRAINT IF EXISTS user_memberships_role_id_fkey;

DO $$
BEGIN
    IF to_regclass('turing.access_requests') IS NOT NULL THEN
        ALTER TABLE turing.access_requests DROP CONSTRAINT IF EXISTS access_requests_tenant_id_fkey;
        ALTER TABLE turing.access_requests DROP CONSTRAINT IF EXISTS access_requests_requested_role_id_fkey;
    END IF;
    IF to_regclass('brillaint_therapy.students') IS NOT NULL THEN
        ALTER TABLE brillaint_therapy.students DROP CONSTRAINT IF EXISTS students_tenant_id_fkey;
    END IF;
    IF to_regclass('brillaint_therapy.planning_registry') IS NOT NULL THEN
        ALTER TABLE brillaint_therapy.planning_registry DROP CONSTRAINT IF EXISTS planning_registry_tenant_id_fkey;
    END IF;
    IF to_regclass('brillaint_therapy.activity_catalog') IS NOT NULL THEN
        ALTER TABLE brillaint_therapy.activity_catalog DROP CONSTRAINT IF EXISTS activity_catalog_tenant_id_fkey;
    END IF;
END $$;

-- ── 2. Tenant: 00000000-0000-0000-0000-000000000001 → 951ed44f-... ──────────
UPDATE turing.tenants SET id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
 WHERE id = '00000000-0000-0000-0000-000000000001';

UPDATE turing.roles            SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
 WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
UPDATE turing.user_memberships SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
 WHERE tenant_id = '00000000-0000-0000-0000-000000000001';

DO $$
BEGIN
    IF to_regclass('turing.access_requests') IS NOT NULL THEN
        UPDATE turing.access_requests SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
         WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
    END IF;
    -- Las columnas tenant_id de las tablas de negocio solo existen si ya corrió la 004
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'students' AND column_name = 'tenant_id') THEN
        UPDATE brillaint_therapy.students SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
         WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'planning_registry' AND column_name = 'tenant_id') THEN
        UPDATE brillaint_therapy.planning_registry SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
         WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'activity_catalog' AND column_name = 'tenant_id') THEN
        UPDATE brillaint_therapy.activity_catalog SET tenant_id = '951ed44f-2c83-4dfc-af59-0feb84beffff'
         WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
    END IF;
END $$;

-- ── 3. Roles ─────────────────────────────────────────────────────────────────
-- admin
UPDATE turing.roles SET id = '98492cd2-d487-46aa-9e63-2f5063d9bf3a'
 WHERE id = '00000000-0000-0000-0000-000000000010';
UPDATE turing.user_memberships SET role_id = '98492cd2-d487-46aa-9e63-2f5063d9bf3a'
 WHERE role_id = '00000000-0000-0000-0000-000000000010';
-- terapeuta
UPDATE turing.roles SET id = '150a8019-9193-4b84-8994-bb6decae1ac1'
 WHERE id = '00000000-0000-0000-0000-000000000011';
UPDATE turing.user_memberships SET role_id = '150a8019-9193-4b84-8994-bb6decae1ac1'
 WHERE role_id = '00000000-0000-0000-0000-000000000011';
-- padre
UPDATE turing.roles SET id = '69818f7d-9568-458e-b215-c8c9f0bbaf60'
 WHERE id = '00000000-0000-0000-0000-000000000012';
UPDATE turing.user_memberships SET role_id = '69818f7d-9568-458e-b215-c8c9f0bbaf60'
 WHERE role_id = '00000000-0000-0000-0000-000000000012';
-- alumno
UPDATE turing.roles SET id = 'db2fdc60-9516-41b4-9ed7-fc1e55100810'
 WHERE id = '00000000-0000-0000-0000-000000000013';
UPDATE turing.user_memberships SET role_id = 'db2fdc60-9516-41b4-9ed7-fc1e55100810'
 WHERE role_id = '00000000-0000-0000-0000-000000000013';

DO $$
BEGIN
    IF to_regclass('turing.access_requests') IS NOT NULL THEN
        UPDATE turing.access_requests SET requested_role_id = '98492cd2-d487-46aa-9e63-2f5063d9bf3a'
         WHERE requested_role_id = '00000000-0000-0000-0000-000000000010';
        UPDATE turing.access_requests SET requested_role_id = '150a8019-9193-4b84-8994-bb6decae1ac1'
         WHERE requested_role_id = '00000000-0000-0000-0000-000000000011';
        UPDATE turing.access_requests SET requested_role_id = '69818f7d-9568-458e-b215-c8c9f0bbaf60'
         WHERE requested_role_id = '00000000-0000-0000-0000-000000000012';
        UPDATE turing.access_requests SET requested_role_id = 'db2fdc60-9516-41b4-9ed7-fc1e55100810'
         WHERE requested_role_id = '00000000-0000-0000-0000-000000000013';
    END IF;
END $$;

-- ── 4. Recrear las FKs (solo las de tablas/columnas que existen) ────────────
ALTER TABLE turing.roles
  ADD CONSTRAINT roles_tenant_id_fkey
  FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;

ALTER TABLE turing.user_memberships
  ADD CONSTRAINT user_memberships_tenant_id_fkey
  FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;

ALTER TABLE turing.user_memberships
  ADD CONSTRAINT user_memberships_role_id_fkey
  FOREIGN KEY (role_id) REFERENCES turing.roles(id) ON DELETE CASCADE;

DO $$
BEGIN
    IF to_regclass('turing.access_requests') IS NOT NULL THEN
        ALTER TABLE turing.access_requests
          ADD CONSTRAINT access_requests_tenant_id_fkey
          FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;
        ALTER TABLE turing.access_requests
          ADD CONSTRAINT access_requests_requested_role_id_fkey
          FOREIGN KEY (requested_role_id) REFERENCES turing.roles(id) ON DELETE SET NULL;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'students' AND column_name = 'tenant_id') THEN
        ALTER TABLE brillaint_therapy.students
          ADD CONSTRAINT students_tenant_id_fkey
          FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'planning_registry' AND column_name = 'tenant_id') THEN
        ALTER TABLE brillaint_therapy.planning_registry
          ADD CONSTRAINT planning_registry_tenant_id_fkey
          FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'activity_catalog' AND column_name = 'tenant_id') THEN
        ALTER TABLE brillaint_therapy.activity_catalog
          ADD CONSTRAINT activity_catalog_tenant_id_fkey
          FOREIGN KEY (tenant_id) REFERENCES turing.tenants(id) ON DELETE CASCADE;
    END IF;
END $$;

COMMIT;
