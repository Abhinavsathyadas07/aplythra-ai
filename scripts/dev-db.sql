-- Dev/CI database bootstrap. Dev-only passwords; never reuse them anywhere real.
-- jobpilot_owner runs migrations and owns tables; jobpilot_app is the runtime role (subject to RLS).
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jobpilot_owner') THEN
    CREATE ROLE jobpilot_owner LOGIN PASSWORD 'dev_owner_pw' NOSUPERUSER NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jobpilot_app') THEN
    CREATE ROLE jobpilot_app LOGIN PASSWORD 'dev_app_pw' NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
SELECT 'CREATE DATABASE jobpilot OWNER jobpilot_owner'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jobpilot')\gexec
SELECT 'CREATE DATABASE jobpilot_test OWNER jobpilot_owner'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'jobpilot_test')\gexec
