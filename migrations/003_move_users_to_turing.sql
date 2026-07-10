-- 003_move_users_to_turing.sql
--
-- Mueve la identidad de usuario del schema de tenant (brillaint_therapy.users)
-- al schema global (turing.users). El usuario es una identidad GLOBAL de la
-- plataforma: una fila por persona, membresías por tenant en turing.user_memberships.
--
-- Estrategia:
--   1. Crear turing.users (misma estructura que la tabla real) + trigger updated_at.
--   2. Copiar todos los datos.
--   3. Re-apuntar las 3 FKs que referencian a la tabla vieja:
--      turing.user_memberships.user_id, brillaint_therapy.planning_registry.author_id,
--      brillaint_therapy.student_guardians.guardian_id.
--   4. Renombrar la tabla vieja a users_legacy (NO se borra: rollback = renombrar de
--      vuelta y re-apuntar FKs). Se eliminará en una migración futura tras verificar.
--
-- Requiere: 001 y 002 aplicadas. Idempotente: si turing.users ya existe y la tabla
-- legacy ya fue renombrada, no hace nada.

BEGIN;

-- 1. Función de trigger para updated_at en schema turing
CREATE OR REPLACE FUNCTION turing.update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Tabla global de usuarios
CREATE TABLE IF NOT EXISTS turing.users (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email                  varchar(255) UNIQUE NOT NULL,
    password_hash          varchar(255) NOT NULL,
    full_name              varchar(100) NOT NULL,
    role                   varchar(50) NOT NULL DEFAULT 'user',
    is_active              boolean DEFAULT true,
    created_at             timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at             timestamptz DEFAULT CURRENT_TIMESTAMP,
    reset_password_token   varchar(255),
    reset_password_expires timestamptz
);

DROP TRIGGER IF EXISTS update_users_modtime ON turing.users;
CREATE TRIGGER update_users_modtime
    BEFORE UPDATE ON turing.users
    FOR EACH ROW EXECUTE FUNCTION turing.update_updated_at_column();

-- 3. Copiar datos (solo si la tabla legacy aún existe con su nombre original)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'users') THEN
        INSERT INTO turing.users
            (id, email, password_hash, full_name, role, is_active,
             created_at, updated_at, reset_password_token, reset_password_expires)
        SELECT id, email, password_hash, full_name, role, is_active,
               created_at, updated_at, reset_password_token, reset_password_expires
        FROM brillaint_therapy.users
        ON CONFLICT (id) DO NOTHING;
    END IF;
END $$;

-- 4. Re-apuntar FKs hacia turing.users
DO $$
BEGIN
    -- turing.user_memberships.user_id
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
               WHERE constraint_name = 'user_memberships_user_id_fkey'
                 AND table_schema = 'turing') THEN
        ALTER TABLE turing.user_memberships DROP CONSTRAINT user_memberships_user_id_fkey;
    END IF;
    ALTER TABLE turing.user_memberships
        ADD CONSTRAINT user_memberships_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES turing.users(id) ON DELETE CASCADE;

    -- brillaint_therapy.planning_registry.author_id
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
               WHERE constraint_name = 'planning_registry_author_id_fkey'
                 AND table_schema = 'brillaint_therapy') THEN
        ALTER TABLE brillaint_therapy.planning_registry DROP CONSTRAINT planning_registry_author_id_fkey;
    END IF;
    ALTER TABLE brillaint_therapy.planning_registry
        ADD CONSTRAINT planning_registry_author_id_fkey
        FOREIGN KEY (author_id) REFERENCES turing.users(id);

    -- brillaint_therapy.student_guardians.guardian_id
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
               WHERE constraint_name = 'student_guardians_guardian_id_fkey'
                 AND table_schema = 'brillaint_therapy') THEN
        ALTER TABLE brillaint_therapy.student_guardians DROP CONSTRAINT student_guardians_guardian_id_fkey;
    END IF;
    ALTER TABLE brillaint_therapy.student_guardians
        ADD CONSTRAINT student_guardians_guardian_id_fkey
        FOREIGN KEY (guardian_id) REFERENCES turing.users(id) ON DELETE CASCADE;
END $$;

-- 5. Renombrar la tabla vieja (falla ruidosa para código rezagado; rollback posible)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'brillaint_therapy' AND table_name = 'users') THEN
        ALTER TABLE brillaint_therapy.users RENAME TO users_legacy;
    END IF;
END $$;

COMMIT;
