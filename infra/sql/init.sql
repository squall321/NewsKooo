-- NewsKoo PostgreSQL bootstrap: role, database, extensions.
-- Run once against a fresh cluster (the dev-services script does this).
-- Idempotent where practical.

-- Extensions are created inside the target DB by Alembic's baseline migration
-- as well; this file ensures the role/db exist for local dev.

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'newskoo') THEN
      CREATE ROLE newskoo LOGIN PASSWORD 'newskoo';
   END IF;
END
$$;

-- (CREATE DATABASE cannot run inside a DO block / transaction; the
--  dev-services script creates the DB separately, then runs the lines below
--  against it.)

-- The following are also handled by the Alembic baseline migration:
--   CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector
--   CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- trigram fuzzy search
