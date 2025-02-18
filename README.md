# YouTube Video Processor

## 最近の更新
- YouTubeの認証: ブラウザのCookieを直接使用するように改善
- Supabaseへのファイルアップロード処理を安定化

## 主な機能
- YouTube動画のダウンロード
- スクリーンショットの自動生成
- 文字起こしと翻訳
- Supabaseでのファイル管理

## 技術的な詳細

### YouTubeの認証
ブラウザのCookieを直接使用することで、より安定した認証を実現：
```python
# yt-dlpの設定
{
    'cookiesfrombrowser': ('chrome',),  # ブラウザのCookieを使用
    'verbose': True,  # デバッグ用
}
```

重要なCookie:
- VISITOR_INFO1_LIVE
- LOGIN_INFO
- SID
- HSID
- __Secure-1PSID

### Supabaseファイルアップロード
安定したファイルアップロード処理：
```python
async def upload_to_supabase(file_path: str, content_type: str, bucket: str) -> str:
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # アップロード実行
    response = supabase.storage \
        .from_(bucket) \
        .upload(unique_filename, file_data)
    
    # 公開URLの取得
    public_url = supabase.storage \
        .from_(bucket) \
        .get_public_url(unique_filename)
```

## セットアップ

1. 環境変数の設定:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
```

2. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

3. アプリケーションの起動:
```bash
vercel dev
```

## 注意点
- YouTubeの認証はブラウザのCookieを使用するため、ブラウザにログインしている必要があります
- Supabaseのストレージバケット'videos'が必要です

## 機能

- YouTube動画のダウンロード
- スクリーンショットの自動生成
- 音声の文字起こし（Whisper API）
- 日本語から英語への翻訳（GPT-4）
- Supabaseによるファイル管理とユーザー認証

## 技術スタック

- **バックエンド**: FastAPI
- **フロントエンド**: TailwindCSS
- **データベース**: Supabase
- **AI/ML**: OpenAI (Whisper API, GPT-4)
- **認証**: Supabase Auth (Google OAuth)
- **ストレージ**: Supabase Storage

## Supabaseの設定

1. **バケットの作成**:
- `videos`バケットを作成（Public access）

2. **テーブルの作成**:
```sql
-- videos テーブル
create table videos (
  id uuid default uuid_generate_v4() primary key,
  youtube_id text,
  youtube_url text not null,
  video_path text,
  transcription text,
  translation text,
  thumbnail_url text,
  duration integer,
  created_at timestamp with time zone default timezone('utc'::text, now()),
  updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- projects テーブル
create table projects (
  id uuid default uuid_generate_v4() primary key,
  video_url text not null,
  video_path text,
  screenshots jsonb default '[]'::jsonb,
  status text default 'pending',
  error_message text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()),
  updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- processing_logs テーブル
create table processing_logs (
  id uuid default uuid_generate_v4() primary key,
  video_id uuid references videos(id),
  status text not null,
  message text,
  created_at timestamp with time zone default timezone('utc'::text, now())
);
```

## 制限事項

- 動画の長さは180秒（3分）まで
- 対応フォーマット: MP4
- 必要なストレージ容量: 動画サイズの約2倍

## デプロイ

Vercelへのデプロイ:
```bash
vercel
```

## ライセンス

MIT

## 作者

ボンポン

## 詳細設定ガイド

### Google OAuth設定

1. **Google Cloud Console**:
   - プロジェクトを作成
   - OAuth 2.0クライアントIDを設定
   - 承認済みのリダイレクトURI:
     ```
     http://localhost:3000/auth/callback
     https://your-production-url.vercel.app/auth/callback
     ```

2. **Supabase認証設定**:
   - Authentication → Providers → Google
   - Client ID・Client Secretを設定
   - Redirect URLsを追加:
     ```
     http://localhost:3000/**
     https://your-production-url.vercel.app/**
     ```

### Supabase詳細設定

1. **RLSポリシー**:
   ```sql
   -- videosテーブル
   ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "Public videos are viewable by everyone"
   ON videos FOR SELECT
   USING (true);
   
   CREATE POLICY "Users can insert their own videos"
   ON videos FOR INSERT
   WITH CHECK (auth.role() = 'authenticated');
   
   -- projectsテーブル
   ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
   CREATE POLICY "Users can view their own projects"
   ON projects FOR SELECT
   USING (true);
   
   CREATE POLICY "Users can create projects"
   ON projects FOR INSERT
   WITH CHECK (auth.role() = 'authenticated');
   ```

2. **ストレージポリシー**:
   ```sql
   -- videosバケット
   CREATE POLICY "Videos are publicly accessible"
   ON storage.objects FOR SELECT
   USING (bucket_id = 'videos');
   
   CREATE POLICY "Only authenticated users can upload"
   ON storage.objects FOR INSERT
   WITH CHECK (
     bucket_id = 'videos'
     AND auth.role() = 'authenticated'
   );
   ```

3. **環境別設定**:
   ```bash
   # .env.development
   HOST=0.0.0.0
   PORT=3000
   VERCEL_ENV=development
   
   # .env.production
   HOST=0.0.0.0
   PORT=3000
   VERCEL_ENV=production
   ```