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