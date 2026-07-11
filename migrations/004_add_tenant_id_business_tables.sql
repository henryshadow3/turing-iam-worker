-- 004_add_tenant_id_business_tables.sql
--
-- Aislamiento multi-tenant: añade tenant_id a las tablas de negocio del schema
-- brillaint_therapy (students, planning_registry, activity_catalog), con
-- backfill al tenant brilliant-therapy y FK a turing.tenants.
--
-- Además, la unicidad del catálogo pasa de global (name) a por tenant
-- (tenant_id, name): cada tenant tiene su propio catálogo.
--
-- Idempotente. Requiere: 001 aplicada (turing.tenants).

BEGIN;

-- Reparación previa: activity_catalog tiene el trigger update_activities_modtime
-- (setea NEW.updated_at) pero la columna updated_at nunca existió, así que TODO
-- UPDATE sobre la tabla fallaba. Se añade la columna para que el trigger funcione.
ALTER TABLE brillaint_therapy.activity_catalog
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT CURRENT_TIMESTAMP;

DO $$
DECLARE
    default_tenant uuid := '951ed44f-2c83-4dfc-af59-0feb84beffff';
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['students', 'planning_registry', 'activity_catalog']
    LOOP
        -- Columna
        EXECUTE format(
            'ALTER TABLE brillaint_therapy.%I ADD COLUMN IF NOT EXISTS tenant_id uuid', t
        );
        -- Backfill al tenant brilliant-therapy
        EXECUTE format(
            'UPDATE brillaint_therapy.%I SET tenant_id = %L WHERE tenant_id IS NULL',
            t, default_tenant
        );
        -- NOT NULL
        EXECUTE format(
            'ALTER TABLE brillaint_therapy.%I ALTER COLUMN tenant_id SET NOT NULL', t
        );
        -- FK a turing.tenants
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = t || '_tenant_id_fkey'
              AND table_schema = 'brillaint_therapy'
        ) THEN
            EXECUTE format(
                'ALTER TABLE brillaint_therapy.%I
                 ADD CONSTRAINT %I FOREIGN KEY (tenant_id)
                 REFERENCES turing.tenants(id)',
                t, t || '_tenant_id_fkey'
            );
        END IF;
        -- Índice para el filtrado por tenant
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON brillaint_therapy.%I (tenant_id)',
            'idx_' || t || '_tenant', t
        );
    END LOOP;
END $$;

-- Catálogo: unicidad por tenant en lugar de global
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'unique_activity_name'
          AND table_schema = 'brillaint_therapy'
    ) THEN
        ALTER TABLE brillaint_therapy.activity_catalog DROP CONSTRAINT unique_activity_name;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'unique_activity_name_per_tenant'
          AND table_schema = 'brillaint_therapy'
    ) THEN
        ALTER TABLE brillaint_therapy.activity_catalog
            ADD CONSTRAINT unique_activity_name_per_tenant UNIQUE (tenant_id, name);
    END IF;
END $$;

COMMIT;
