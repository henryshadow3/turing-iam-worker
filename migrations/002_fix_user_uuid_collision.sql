-- 002_fix_user_uuid_collision.sql
--
-- Problema: seed_data.py insertó usuarios con UUIDs fijos (...0001, ...0002) y
-- ...0001 es TAMBIÉN el UUID del tenant brilliant-therapy. Esa colisión alimenta
-- el bug de DEFAULT_THERAPIST_ID (un tenant_id usado como author_id).
--
-- Solución: reasignar un UUID nuevo a cualquier usuario cuyo id colisione con un
-- tenant, re-apuntando todas las referencias (planning_registry.author_id,
-- student_guardians.guardian_id, user_memberships.user_id).
--
-- Idempotente: si no hay colisiones, no hace nada.

BEGIN;

DO $$
DECLARE
    colliding RECORD;
    new_id uuid;
BEGIN
    FOR colliding IN
        SELECT u.id
        FROM brillaint_therapy.users u
        WHERE EXISTS (SELECT 1 FROM turing.tenants t WHERE t.id = u.id)
    LOOP
        new_id := gen_random_uuid();

        -- Copia del usuario con el UUID nuevo (email temporal para no chocar con UNIQUE)
        INSERT INTO brillaint_therapy.users
            (id, email, password_hash, full_name, role, is_active,
             created_at, updated_at, reset_password_token, reset_password_expires)
        SELECT new_id, email || '.tmp-collision', password_hash, full_name, role, is_active,
               created_at, updated_at, reset_password_token, reset_password_expires
        FROM brillaint_therapy.users
        WHERE id = colliding.id;

        -- Re-apuntar todas las referencias al usuario viejo
        UPDATE brillaint_therapy.planning_registry SET author_id   = new_id WHERE author_id   = colliding.id;
        UPDATE brillaint_therapy.student_guardians SET guardian_id = new_id WHERE guardian_id = colliding.id;
        UPDATE turing.user_memberships             SET user_id     = new_id WHERE user_id     = colliding.id;

        -- Eliminar el usuario viejo y restaurar el email original
        DELETE FROM brillaint_therapy.users WHERE id = colliding.id;
        UPDATE brillaint_therapy.users
        SET email = replace(email, '.tmp-collision', '')
        WHERE id = new_id;

        RAISE NOTICE 'Usuario % reasignado a nuevo UUID %', colliding.id, new_id;
    END LOOP;
END $$;

COMMIT;
