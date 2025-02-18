# YouTube Transcriber

YouTubeの動画を文字起こし・翻訳するWebアプリケーション

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

## セットアップ

1. **環境変数の設定**:
```bash
cp .env.sample .env.development
```

必要な環境変数:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4o-mini-2024-07-18
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

2. **依存関係のインストール**:
```bash
pip install -r requirements.txt
```

3. **開発サーバーの起動**:
```bash
uvicorn app:app --reload
```

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

## 最近の更新

- Supabaseストレージのアップロード処理を改善
- エラーハンドリングの強化
- UI/UXの改善

## セキュリティ注意事項

- `service_role`キーは公開しない
- 本番環境では適切なRLSポリシーを設定
- 環境変数は適切に管理

## Google認証の実装方法

1. **Supabaseでの設定**:
   - Supabaseプロジェクトの認証設定でGoogleプロバイダーを有効化
   - Google Cloud Consoleで認証情報を作成し、クライアントIDとシークレットを取得
   - Supabaseの認証設定にGoogle認証情報を設定

2. **環境変数の設定**:
   ```bash
   # .env.development
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

3. **フロントエンド実装**:
   ```html
   <!-- Supabase JSクライアントの読み込み -->
   <script src="https://unpkg.com/@supabase/supabase-js@2"></script>

   <!-- ログインボタン -->
   <button onclick="handleGoogleSignIn()" class="bg-blue-500 text-white px-4 py-2 rounded">
       Googleでログイン
   </button>

   <script>
   // Supabaseクライアントの初期化
   const supabase = supabase.createClient(
       '{{ config.SUPABASE_URL }}',
       '{{ config.SUPABASE_ANON_KEY }}'
   );

   // Google認証ハンドラ
   async function handleGoogleSignIn() {
       const { data, error } = await supabase.auth.signInWithOAuth({
           provider: 'google',
           options: {
               redirectTo: window.location.origin
           }
       });

       if (error) {
           console.error('Error:', error.message);
           alert('ログインに失敗しました: ' + error.message);
       }
   }
   </script>
   ```

4. **バックエンド実装**:
   ```python
   @app.get("/auth/callback")
   async def auth_callback(request: Request):
       try:
           # セッショントークンの取得
           access_token = request.cookies.get("sb-access-token")
           refresh_token = request.cookies.get("sb-refresh-token")
           
           if not access_token:
               raise HTTPException(status_code=401, detail="No session token")
               
           return RedirectResponse(url="/")
           
       except Exception as e:
           print(f"Auth callback error: {str(e)}")
           raise HTTPException(status_code=400, detail=str(e))
   ```

# YouTube Transcriber

## 環境設定

### Supabase設定
1. **URL Configuration**:
   - Site URL: `https://youtube-downloader-rnw5guisn-bonginkan-projects.vercel.app`
   - Redirect URLs:
     - `http://localhost:3000`
     - `https://youtube-downloader-rnw5guisn-bonginkan-projects.vercel.app/auth/callback`

2. **環境変数**:
   ```bash
   # 開発環境 (.env.development)
   NEXT_PUBLIC_SITE_URL=http://localhost:3000

   # 本番環境 (Vercel)
   NEXT_PUBLIC_SITE_URL=https://youtube-downloader-rnw5guisn-bonginkan-projects.vercel.app
   ```

### 認証フロー
1. ユーザーがログインボタンをクリック
2. Googleログイン画面表示
3. 認証後、環境に応じたURLにリダイレクト:
   - 開発環境: `http://localhost:3000`
   - 本番環境: `https://youtube-downloader-rnw5guisn-bonginkan-projects.vercel.app`

### ファイルアップロード
1. **一時ファイルの保存**:
   ```python
   TEMP_DIR = "/tmp"
   DOWNLOAD_DIR = f"{TEMP_DIR}/downloads"
   SCREENSHOT_DIR = f"{TEMP_DIR}/screenshots"
   ```

2. **Supabaseストレージ**:
   - バケット: `videos`
   - アップロード処理:
     ```python
     upload_response = supabase.storage.from_(bucket).upload(
         path=file_name,
         file=file_data,
         file_options={"content-type": content_type}
     )
     ```

## 開発環境
1. **ローカル開発**:
   ```bash
   vercel dev
   ```

2. **本番デプロイ**:
   ```bash
   vercel deploy --prod
   ```

## 注意点
1. 環境変数は`.env.development`と`.env`で管理
2. Supabaseの設定は開発/本番環境で共通
3. 認証コールバックは環境に応じて動的に切り替え

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