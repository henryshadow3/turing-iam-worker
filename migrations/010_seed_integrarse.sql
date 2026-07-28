-- 010_seed_integrarse.sql
-- Tenant y rol inicial para el acceso protegido al Templo Integrarse.
-- Idempotente: puede ejecutarse varias veces sin duplicar datos.

BEGIN;

INSERT INTO turing.tenants (id, slug, name, redirect_url, is_active, created_at)
SELECT gen_random_uuid(), 'integrarse', 'Integrarse',
       'https://integrarse.net/interior/', true, now()
WHERE NOT EXISTS (
    SELECT 1 FROM turing.tenants WHERE slug = 'integrarse'
);

UPDATE turing.tenants
SET name = 'Integrarse',
    redirect_url = 'https://integrarse.net/interior/',
    is_active = true
WHERE slug = 'integrarse';

INSERT INTO turing.roles (id, tenant_id, name, is_active, created_at)
SELECT gen_random_uuid(), t.id, 'Probacionista', true, now()
FROM turing.tenants t
WHERE t.slug = 'integrarse'
  AND NOT EXISTS (
      SELECT 1
      FROM turing.roles r
      WHERE r.tenant_id = t.id AND lower(r.name) = lower('Probacionista')
  );

UPDATE turing.roles r
SET is_active = true
FROM turing.tenants t
WHERE r.tenant_id = t.id
  AND t.slug = 'integrarse'
  AND lower(r.name) = lower('Probacionista');

COMMIT;
