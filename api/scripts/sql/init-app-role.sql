-- Create the runtime DB role used by the application at request time.
--
-- The role is deliberately NOSUPERUSER + NOBYPASSRLS so the
-- `*_tenant_isolation` RLS policies (created by Alembic) actually fire.
-- Migrations continue to run as the cluster owner (the connection string
-- in `DB_MIGRATION_USER` / `DB_MIGRATION_PASSWORD`, default `postgres`).
--
-- This script is idempotent. Re-running is safe.
--
-- Run via:
--     docker exec -i magnet-postgres \
--         psql -U postgres -d magnet_dev \
--         < api/scripts/sql/init-app-role.sql

DO $$
DECLARE
    target_role   text := 'magnet_app';
    target_pwd    text := COALESCE(
        current_setting('magnet.app_password', true),
        'magnet_app_dev_pw'
    );
    target_db     text := current_database();
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = target_role) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB INHERIT',
            target_role, target_pwd
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE %I LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB INHERIT',
            target_role
        );
    END IF;

    EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I', target_db, target_role);
END
$$;

-- Schema + DML access on everything that exists today.
-- CREATE on `public` is needed because TaskIQ creates its own
-- bookkeeping tables (`taskiq_results`, `taskiq_schedules`) on broker
-- startup via `CREATE TABLE IF NOT EXISTS`. The IF-NOT-EXISTS clause
-- still checks CREATE privilege even when the table already exists.
GRANT USAGE, CREATE ON SCHEMA public TO magnet_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO magnet_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO magnet_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO magnet_app;

-- Default privileges for objects created later by `postgres` (alembic).
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO magnet_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO magnet_app;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO magnet_app;

-- TaskIQ creates and then alters its own bookkeeping tables on broker
-- startup (CREATE INDEX, ALTER TABLE). If the tables already exist
-- under another owner, that fails with `must be owner of table …`.
-- Reassign so the app role owns them outright.
DO $$
DECLARE
    tbl text;
BEGIN
    FOREACH tbl IN ARRAY ARRAY['taskiq_messages','taskiq_results','taskiq_schedules']
    LOOP
        IF EXISTS (
            SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=tbl
        ) THEN
            EXECUTE format('ALTER TABLE public.%I OWNER TO magnet_app', tbl);
        END IF;
    END LOOP;
END
$$;

-- Sanity: confirm the role can't bypass RLS.
DO $$
DECLARE
    rolsuper bool;
    rolbypassrls bool;
BEGIN
    SELECT r.rolsuper, r.rolbypassrls
        INTO rolsuper, rolbypassrls
        FROM pg_roles r WHERE rolname = 'magnet_app';
    IF rolsuper OR rolbypassrls THEN
        RAISE EXCEPTION
            'magnet_app role must be NOSUPERUSER + NOBYPASSRLS (got super=%, bypass=%)',
            rolsuper, rolbypassrls;
    END IF;
END
$$;
