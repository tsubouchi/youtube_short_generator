# YouTube Video Processing API

FastAPIとSupabaseを使用したYouTubeショート動画の処理APIです。

## 機能

- YouTube動画のダウンロード（3分以内）
- スクリーンショットの自動生成
- OpenAI Whisperによる文字起こし
- GPT-4による英語翻訳
- Supabaseでのデータ管理

## 必要な環境変数

```env
# Supabase設定
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI設定
OPENAI_API_KEY=your-openai-key
AI_MODEL=gpt-4o-mini-2024-07-18

# データベース設定
DATABASE_URL=your-database-url

# Google Auth
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Supabase設定の重要事項

### 1. RLSポリシー設定

以下のSQLを実行してRLSポリシーを設定：

```sql
-- RLSを有効化
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;

-- プロジェクトテーブルのポリシー
CREATE POLICY "enable_all_projects_access"
ON projects FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);

-- ビデオテーブルのポリシー
CREATE POLICY "enable_all_videos_access"
ON videos FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);

-- ログテーブルのポリシー
CREATE POLICY "enable_all_logs_access"
ON processing_logs FOR ALL
TO anon, authenticated
USING (true)
WITH CHECK (true);
```

### 2. 権限設定

```sql
-- すべてのテーブルに対する権限を付与
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- service_roleに対する権限を付与
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- authenticatedロールに対する権限を付与
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
```

### 3. 重要な注意事項

- 本番環境では`service_role`キーを使用すること
- 環境変数は`.env.local`で管理
- Vercel環境変数も適切に設定すること

## インストールと実行

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
```bash
cp .env.example .env.local
# .env.localを編集
```

3. アプリケーションの起動:
```bash
vercel dev
```

## Vercelへのデプロイ

1. 環境変数の設定:
```bash
vercel env add SUPABASE_KEY
vercel env add OPENAI_API_KEY
# 他の必要な環境変数も同様に設定
```

2. デプロイ:
```bash
vercel deploy
```

## エラー対応

1. データベースアクセスエラー:
- RLSポリシーの確認
- `service_role`キーの使用確認
- 権限設定の確認

2. ファイルアップロードエラー:
- Supabaseストレージバケットの権限確認
- 一時ファイルパスの確認

## セキュリティ注意事項

- `service_role`キーは公開しない
- 本番環境では適切なRLSポリシーを設定
- 環境変数は適切に管理

## ライセンス

MIT License

## Google認証の設定

### 1. Google Cloud Consoleでの設定
1. [Google Cloud Console](https://console.cloud.google.com/)で新しいプロジェクトを作成
2. OAuth同意画面を設定
3. 認証情報 → OAuth 2.0 クライアントIDを作成
   - 承認済みのリダイレクトURI: `https://[YOUR_SUPABASE_PROJECT].supabase.co/auth/v1/callback`

### 2. Supabaseでの設定
1. Authentication → Providers → Googleを有効化
2. Google Cloud ConsoleのクライアントIDとシークレットを設定
3. Redirect URLをGoogle Cloud Consoleに追加

### 3. 環境変数の追加
```env
# Google Auth
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Google OAuth設定

### 認証情報
```json
{
  "web": {
    "client_id": "your-google-client-id",
    "project_id": "velvety-pagoda-451303-m6",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-google-client-secret",
    "redirect_uris": [
      "http://localhost:8000/auth/google/callback",
      "https://youtube-downloader-dun.vercel.app/auth/google/callback",
      "https://ygxobaodxtmbmxowidoh.supabase.co/auth/v1/callback"
    ],
    "javascript_origins": [
      "http://localhost:8000",
      "https://youtube-downloader-dun.vercel.app"
    ]
  }
}
```

### 環境変数設定
```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```