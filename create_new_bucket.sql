-- Create a new public bucket for verification documents
-- Run these commands in your Supabase SQL Editor with service_role key

-- 1. Create the bucket (public by default)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'verification-docs',
    'verification-docs', 
    true,
    52428800, -- 50MB limit
    ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
);

-- 2. Enable RLS on storage.objects if not already enabled
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. Create policy to allow public INSERT (upload)
CREATE POLICY "Public can upload to verification-docs"
ON storage.objects
FOR INSERT
TO public
WITH CHECK (bucket_id = 'verification-docs');

-- 4. Create policy to allow public SELECT (download/view)
CREATE POLICY "Public can view verification-docs"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'verification-docs');

-- 5. Create policy to allow public UPDATE
CREATE POLICY "Public can update verification-docs"
ON storage.objects
FOR UPDATE
TO public
USING (bucket_id = 'verification-docs')
WITH CHECK (bucket_id = 'verification-docs');

-- 6. Create policy to allow public DELETE
CREATE POLICY "Public can delete verification-docs"
ON storage.objects
FOR DELETE
TO public
USING (bucket_id = 'verification-docs');

-- 7. Enable RLS on storage.buckets if not already enabled
ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

-- 8. Create policy to allow public access to the bucket metadata
CREATE POLICY "Public can access verification-docs bucket"
ON storage.buckets
FOR SELECT
TO public
USING (id = 'verification-docs');

-- 9. Verify the bucket was created
SELECT id, name, public, file_size_limit, allowed_mime_types 
FROM storage.buckets 
WHERE id = 'verification-docs';

-- 10. Verify the policies were created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('objects', 'buckets') 
AND schemaname = 'storage'
AND policyname LIKE '%verification-docs%';