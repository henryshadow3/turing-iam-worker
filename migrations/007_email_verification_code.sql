-- 007_email_verification_code.sql
-- Cambia la verificación de email de link UUID a código de 6 dígitos con expiración.

BEGIN;

ALTER TABLE turing.users
    DROP COLUMN IF EXISTS email_verification_token,
    ADD COLUMN IF NOT EXISTS email_verification_code VARCHAR(6) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS email_verification_code_expires TIMESTAMPTZ DEFAULT NULL;

COMMIT;
