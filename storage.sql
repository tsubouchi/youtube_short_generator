-- バケットの作成
INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('videos', 'videos', true),
  ('screenshots', 'screenshots', true)
ON CONFLICT (id) DO NOTHING;

-- バケットのポリシー設定
CREATE POLICY "Videos are publicly accessible"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'videos');

CREATE POLICY "Screenshots are publicly accessible"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'screenshots');

CREATE POLICY "Anyone can upload videos"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'videos');

CREATE POLICY "Anyone can upload screenshots"
  ON storage.objects FOR INSERT
  WITH CHECK (bucket_id = 'screenshots');