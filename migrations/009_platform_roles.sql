-- 009: Normaliza turing.users.role a roles de PLATAFORMA.
--
-- turing.users.role es el rol de plataforma Turing (quién puede operar el IAM),
-- NO el rol dentro de un tenant (ese vive en user_memberships → turing.roles).
-- La migración 003 copió el role heredado de brillaint_therapy.users, dejando
-- valores de tenant ('terapeuta', 'padre', 'alumno') como rol de plataforma.
--
-- Roles de plataforma válidos: user | analista | developer | admin | superadmin
-- Los usuarios de negocio (terapeutas de Brilliant) pasan a 'user': su rol de
-- terapeuta sigue intacto en su membresía, que es lo que autoriza el dashboard.
--
-- Idempotente: el UPDATE es no-op si ya no quedan roles de tenant en users.
-- OJO: 'admin' NO se toca — a partir de aquí significa admin de plataforma.

BEGIN;

UPDATE turing.users
SET role = 'user', updated_at = now()
WHERE role IN ('terapeuta', 'padre', 'alumno', 'director', 'maestro', 'administrador');

COMMIT;
