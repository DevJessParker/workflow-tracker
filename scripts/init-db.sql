-- Initialize Pinata Code Database
-- This script runs on first database startup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schema for application
CREATE SCHEMA IF NOT EXISTS pinata;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA pinata TO postgres;
GRANT ALL PRIVILEGES ON DATABASE pinata_dev TO postgres;

-- Log initialization
DO $$
BEGIN
  RAISE NOTICE '🪅 Pinata Code database initialized successfully!';
  RAISE NOTICE '✅ Extensions created: uuid-ossp, pg_trgm';
  RAISE NOTICE '✅ Schema created: pinata';
END $$;
