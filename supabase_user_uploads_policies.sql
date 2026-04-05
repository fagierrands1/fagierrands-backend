-- Supabase Storage Policies for user-uploads bucket
-- Run these commands in your Supabase SQL Editor

-- 1. First, create the user-uploads bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-uploads', 'user-uploads', false)
ON CONFLICT (id) DO NOTHING;

-- 2. Ensure RLS is enabled on the storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. Allow service role to INSERT files into user-uploads bucket
CREATE POLICY "Allow service role upload to user-uploads" 
ON storage.objects 
FOR INSERT 
TO authenticated, anon, service_role
WITH CHECK (bucket_id = 'user-uploads');

-- 4. Allow service role to SELECT (view) files from user-uploads bucket
CREATE POLICY "Allow service role view user-uploads" 
ON storage.objects 
FOR SELECT 
TO authenticated, anon, service_role
USING (bucket_id = 'user-uploads');

-- 5. Allow service role to UPDATE files in user-uploads bucket
CREATE POLICY "Allow service role update user-uploads" 
ON storage.objects 
FOR UPDATE 
TO authenticated, anon, service_role
USING (bucket_id = 'user-uploads')
WITH CHECK (bucket_id = 'user-uploads');

-- 6. Allow service role to DELETE files from user-uploads bucket
CREATE POLICY "Allow service role delete user-uploads" 
ON storage.objects 
FOR DELETE 
TO authenticated, anon, service_role
USING (bucket_id = 'user-uploads');

-- 7. Ensure the bucket itself is accessible
ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

-- Allow access to the user-uploads bucket
CREATE POLICY "Allow access to user-uploads bucket" 
ON storage.buckets 
FOR SELECT 
TO authenticated, anon, service_role
USING (id = 'user-uploads');

-- 8. Verify the policies were created (optional check)
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('objects', 'buckets') 
AND schemaname = 'storage'
AND policyname LIKE '%user-uploads%';