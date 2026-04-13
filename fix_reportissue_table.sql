-- Fix for missing orders_reportissue_evidence_photos table
-- This table reference exists in the database but not in the current code

-- Option 1: If the table exists, drop it
DROP TABLE IF EXISTS orders_reportissue_evidence_photos CASCADE;

-- Option 2: If there are foreign key constraints referencing it, drop them
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT constraint_name, table_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND constraint_name LIKE '%reportissue_evidence_photos%'
    ) LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.table_name) || 
                ' DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name) || ' CASCADE';
    END LOOP;
END $$;

-- Drop any related sequences
DROP SEQUENCE IF EXISTS orders_reportissue_evidence_photos_id_seq CASCADE;

-- Verify cleanup
SELECT tablename FROM pg_tables WHERE tablename LIKE '%reportissue%';
