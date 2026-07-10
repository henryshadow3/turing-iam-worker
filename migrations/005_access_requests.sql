-- 005_access_requests.sql
--
-- Bandeja de solicitudes de acceso. Cuando alguien se registra desde una landing
-- (p.ej. Brilliant), se crea el usuario global SIN membresía y una solicitud
-- PENDIENTE de acceso a un tenant con un rol sugerido. El superadmin la aprueba
-- (crea la membresía) o la rechaza desde el turing-iam-front.
--
-- Idempotente. Requiere: 001 (tenants/roles) y 003 (turing.users).

BEGIN;

CREATE TABLE IF NOT EXISTS turing.access_requests (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           uuid NOT NULL REFERENCES turing.users(id)   ON DELETE CASCADE,
    tenant_id         uuid NOT NULL REFERENCES turing.tenants(id) ON DELETE CASCADE,
    -- Rol sugerido para la membresía cuando se apruebe (puede cambiarse al aprobar).
    requested_role_id uuid REFERENCES turing.roles(id) ON DELETE SET NULL,
    status            varchar(20) NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    note              varchar(255),
    created_at        timestamptz DEFAULT now() NOT NULL,
    resolved_at       timestamptz,
    -- Superadmin que resolvió la solicitud (auditoría).
    resolved_by       uuid REFERENCES turing.users(id) ON DELETE SET NULL,
    CONSTRAINT access_requests_status_chk
        CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- Solo puede haber UNA solicitud pendiente por (usuario, tenant): evita duplicados
-- si el usuario reintenta el registro. Las ya resueltas no cuentan.
CREATE UNIQUE INDEX IF NOT EXISTS uq_access_requests_pending
    ON turing.access_requests (user_id, tenant_id)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_access_requests_status ON turing.access_requests (status);
CREATE INDEX IF NOT EXISTS idx_access_requests_tenant ON turing.access_requests (tenant_id);

COMMIT;
