-- UUID拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 既存のテーブルを削除
DROP TABLE IF EXISTS video_tags CASCADE;
DROP TABLE IF EXISTS processing_logs CASCADE;
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- タグテーブルの作成
CREATE TABLE tags (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- ビデオテーブルの作成
CREATE TABLE videos (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    youtube_url TEXT NOT NULL,
    youtube_id TEXT,
    video_path TEXT,
    transcription TEXT,
    translation TEXT,
    thumbnail_url TEXT,
    duration INT4,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- ビデオタグ中間テーブルの作成
CREATE TABLE video_tags (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    tag_id UUID REFERENCES tags(id),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    UNIQUE(video_id, tag_id)
);

-- 処理ログテーブルの作成
CREATE TABLE processing_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    status TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- プロジェクトテーブルの作成
CREATE TABLE projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    video_url TEXT NOT NULL,
    video_path TEXT,
    screenshots JSONB DEFAULT '[]',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- インデックスの作成
CREATE INDEX idx_videos_youtube_id ON videos(youtube_id);
CREATE INDEX idx_videos_created_at ON videos(created_at);
CREATE INDEX idx_video_tags_video_id ON video_tags(video_id);
CREATE INDEX idx_video_tags_tag_id ON video_tags(tag_id);
CREATE INDEX idx_processing_logs_video_id ON processing_logs(video_id);
CREATE INDEX idx_processing_logs_status ON processing_logs(status);
CREATE INDEX idx_projects_status ON projects(status);

-- RLSの設定
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE video_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- RLSポリシーの作成
DROP POLICY IF EXISTS "Public videos are viewable by everyone" ON videos;
DROP POLICY IF EXISTS "Public tags are viewable by everyone" ON tags;
DROP POLICY IF EXISTS "Public video_tags are viewable by everyone" ON video_tags;
DROP POLICY IF EXISTS "Public processing_logs are viewable by everyone" ON processing_logs;
DROP POLICY IF EXISTS "Public projects are viewable by everyone" ON projects;

CREATE POLICY "Public videos are viewable by everyone" ON videos FOR SELECT USING (true);
CREATE POLICY "Public tags are viewable by everyone" ON tags FOR SELECT USING (true);
CREATE POLICY "Public video_tags are viewable by everyone" ON video_tags FOR SELECT USING (true);
CREATE POLICY "Public processing_logs are viewable by everyone" ON processing_logs FOR SELECT USING (true);
CREATE POLICY "Public projects are viewable by everyone" ON projects FOR SELECT USING (true);

-- ストレージバケットの設定
INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('videos', 'videos', true),
  ('screenshots', 'screenshots', true)
ON CONFLICT (id) DO NOTHING;

-- ストレージバケットのポリシー設定
DROP POLICY IF EXISTS "Videos are publicly accessible" ON storage.objects;
DROP POLICY IF EXISTS "Screenshots are publicly accessible" ON storage.objects;
DROP POLICY IF EXISTS "Anyone can upload videos" ON storage.objects;
DROP POLICY IF EXISTS "Anyone can upload screenshots" ON storage.objects;

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

-- ビューの作成（最近の処理結果表示用）
CREATE OR REPLACE VIEW recent_projects AS
SELECT 
    id,
    video_url,
    video_path,
    screenshots,
    status,
    created_at,
    updated_at
FROM projects
WHERE created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
ORDER BY created_at DESC;

-- コメント追加
COMMENT ON TABLE projects IS 'YouTube動画処理プロジェクトの管理テーブル';
COMMENT ON COLUMN projects.id IS 'プロジェクトの一意識別子';
COMMENT ON COLUMN projects.video_url IS 'YouTube動画のURL';
COMMENT ON COLUMN projects.video_path IS 'Supabaseストレージ内の動画パス';
COMMENT ON COLUMN projects.screenshots IS 'スクリーンショットのURLリスト（JSONB配列）';
COMMENT ON COLUMN projects.status IS 'プロジェクトの処理状態';
COMMENT ON COLUMN projects.error_message IS 'エラーが発生した場合のメッセージ';
COMMENT ON COLUMN projects.metadata IS '追加のメタデータ（動画の長さ、タイトルなど）';

-- 注意: ストレージバケットの設定はSupabase Dashboardで手動で行う必要があります
-- 1. videosバケット
--    - 作成: CREATE BUCKET IF NOT EXISTS videos
--    - 権限: アップロード=すべてのユーザー, ダウンロード=公開
--
-- 2. screenshotsバケット
--    - 作成: CREATE BUCKET IF NOT EXISTS screenshots
--    - 権限: アップロード=すべてのユーザー, ダウンロード=公開