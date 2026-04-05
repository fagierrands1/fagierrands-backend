-- Fix RLS policies for user-uploads bucket
-- Run this in Supabase SQL Editor

-- 1. Create policy to allow public uploads to user-uploads bucket
CREATE POLICY "Allow public uploads to user-uploads"
ON storage.objects
FOR INSERT
TO public
WITH CHECK (bucket_id = 'user-uploads');

-- 2. Create policy to allow public access to files in user-uploads bucket
CREATE POLICY "Allow public access to user-uploads"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'user-uploads');

-- 3. Allow public updates (optional)
CREATE POLICY "Allow public updates to user-uploads"
ON storage.objects
FOR UPDATE
TO public
USING (bucket_id = 'user-uploads')
WITH CHECK (bucket_id = 'user-uploads');

-- 4. Allow public deletes (optional)
CREATE POLICY "Allow public deletes from user-uploads"
ON storage.objects
FOR DELETE
TO public
USING (bucket_id = 'user-uploads');

-- 5. Verify the bucket exists and is public
SELECT id, name, public FROM storage.buckets WHERE id = 'user-uploads';

-- 6. Check if policies were created
SELECT policyname, cmd, roles 
FROM pg_policies 
WHERE tablename = 'objects' 
AND schemaname = 'storage'
AND policyname LIKE '%user-uploads%';