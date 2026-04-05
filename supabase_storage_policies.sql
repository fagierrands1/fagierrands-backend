-- Supabase Storage Policies for verification-documents bucket
-- Run these commands in your Supabase SQL Editor

-- 1. First, ensure RLS is enabled on the storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 2. Allow authenticated and anonymous users to INSERT files into verification-documents bucket
CREATE POLICY "Allow upload to verification-documents" 
ON storage.objects 
FOR INSERT 
TO public
WITH CHECK (bucket_id = 'verification-documents');

-- 3. Allow authenticated and anonymous users to SELECT (view) files from verification-documents bucket
CREATE POLICY "Allow view verification-documents" 
ON storage.objects 
FOR SELECT 
TO public
USING (bucket_id = 'verification-documents');

-- 4. Allow authenticated and anonymous users to UPDATE files in verification-documents bucket
CREATE POLICY "Allow update verification-documents" 
ON storage.objects 
FOR UPDATE 
TO public
USING (bucket_id = 'verification-documents')
WITH CHECK (bucket_id = 'verification-documents');

-- 5. Allow authenticated and anonymous users to DELETE files from verification-documents bucket
CREATE POLICY "Allow delete verification-documents" 
ON storage.objects 
FOR DELETE 
TO public
USING (bucket_id = 'verification-documents');

-- 6. Also ensure the bucket itself is accessible
-- Enable RLS on buckets table
ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

-- Allow public access to the verification-documents bucket
CREATE POLICY "Allow access to verification-documents bucket" 
ON storage.buckets 
FOR SELECT 
TO public
USING (id = 'verification-documents');

-- 7. Optional: If you want to make the bucket completely public (easier approach)
-- You can also just update the bucket to be public:
UPDATE storage.buckets 
SET public = true 
WHERE id = 'verification-documents';

-- 8. Verify the policies were created (optional check)
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('objects', 'buckets') 
AND schemaname = 'storage';