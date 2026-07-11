-- 006_email_verification.sql
-- Adds email verification support to turing.users.
-- New users start with email_verified = FALSE and must click a link
-- sent to their email before they can access any tenant.

BEGIN;

ALTER TABLE turing.users
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS email_verification_token UUID DEFAULT NULL;

-- Existing users (created before this migration) are trusted — mark them verified.
UPDATE turing.users SET email_verified = TRUE
WHERE email_verified = FALSE;

COMMIT;
