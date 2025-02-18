import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 環境変数の読み込み
load_dotenv()

# Supabaseクライアントの初期化
try:
    supabase: Client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    print("Supabase connection established")

    # バケットの作成
    def create_storage_buckets():
        try:
            # バケットの一覧を取得
            existing_buckets = supabase.storage.list_buckets()
            print("Existing buckets:", existing_buckets)

            # videosバケットの作成
            if 'videos' not in [b['name'] for b in existing_buckets]:
                supabase.storage.create_bucket(
                    'videos',
                    {'public': True}
                )
                print("Videos bucket created successfully")
            else:
                print("Videos bucket already exists")

            # screenshotsバケットの作成
            if 'screenshots' not in [b['name'] for b in existing_buckets]:
                supabase.storage.create_bucket(
                    'screenshots',
                    {'public': True}
                )
                print("Screenshots bucket created successfully")
            else:
                print("Screenshots bucket already exists")

        except Exception as e:
            print(f"Error creating buckets: {str(e)}")

    if __name__ == "__main__":
        create_storage_buckets()

except Exception as e:
    print(f"Supabase connection error: {str(e)}")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
    print(f"SUPABASE_SERVICE_KEY: {os.getenv('SUPABASE_SERVICE_KEY')[:5]}...")  # キーの一部のみを表示 