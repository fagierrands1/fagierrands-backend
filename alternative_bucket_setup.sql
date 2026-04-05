-- Alternative: Simple bucket creation with minimal permissions
-- Try this if the previous approach doesn't work

-- Option 1: Create with a different name
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-uploads', 'user-uploads', true);

-- Option 2: Create with timestamp to ensure uniqueness
INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads-2024', 'uploads-2024', true);

-- Option 3: Very simple approach - just make any existing bucket public
UPDATE storage.buckets 
SET public = true 
WHERE id IN ('verification-documents', 'verification-docs', 'user-uploads');

-- Check what buckets exist
SELECT id, name, public FROM storage.buckets;