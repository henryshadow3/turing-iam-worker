-- 011_evaluacion_inicial_import_idempotency.sql
-- Persistencia idempotente para la importación inicial de evaluaciones.
-- Idempotente: puede ejecutarse varias veces sin duplicar la tabla ni el índice.

BEGIN;

CREATE TABLE IF NOT EXISTS brillaint_therapy.evaluacion_inicial_import_idempotency (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES turing.tenants(id) ON DELETE CASCADE,
    idempotency_key varchar(255) NOT NULL,
    request_hash    varchar(64) NOT NULL,
    response_json   TEXT NOT NULL,
    created_at      timestamptz DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_evaluacion_inicial_import_idempotency_tenant_key
    ON brillaint_therapy.evaluacion_inicial_import_idempotency (tenant_id, idempotency_key);

COMMIT;
