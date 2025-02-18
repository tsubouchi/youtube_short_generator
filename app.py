# FastAPI関連
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# 外部ライブラリ
import yt_dlp
import openai
import ffmpeg
import aiohttp
import certifi
import urllib3
from supabase import create_client, Client
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from yt_dlp.utils import std_headers
import browser_cookie3

# Python標準ライブラリ
import os
import ssl
import uuid
import math
import json
import asyncio
from io import BytesIO
from datetime import datetime, timezone
from typing import Optional, List, Dict
from fastapi import HTTPException
import traceback

# 環境変数の読み込みと検証を関数化
def load_environment():
    load_dotenv('.env.development')  # 明示的に.env.developmentを読み込む
    
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if not youtube_api_key:
        raise ValueError("YOUTUBE_API_KEY is not set")
        
    # 完全なキーの場合のみチェック（開発時のプレースホルダーは許可）
    if youtube_api_key.startswith('AIzaSyC...') and len(youtube_api_key) <= 10:
        raise ValueError("Invalid YOUTUBE_API_KEY format")
        
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'AI_MODEL': os.getenv('AI_MODEL', 'gpt-4o-mini-2024-07-18'),
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
        'YOUTUBE_API_KEY': youtube_api_key
    }
    
    # 必須の環境変数が設定されているか確認
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    print("Loaded environment variables:", {
        k: v[:10] + '...' if v and len(v) > 10 else v 
        for k, v in required_vars.items()
    })
    
    return required_vars

# 環境変数を読み込み
try:
    env_vars = load_environment()
    print("Debug: Environment variables loaded:")
    print(f"Debug: YOUTUBE_API_KEY: {env_vars['YOUTUBE_API_KEY'][:10]}...")
    YOUTUBE_API_KEY = env_vars['YOUTUBE_API_KEY']
except Exception as e:
    print(f"Environment variable error: {str(e)}")
    raise

# FastAPIアプリケーションの作成
app = FastAPI()

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory="templates")

# Supabaseの設定
supabase_url = env_vars['SUPABASE_URL']
supabase_key = env_vars['SUPABASE_KEY']

if not supabase_url or not supabase_key:
    raise Exception("Supabase環境変数が設定されていません")

# Supabaseクライアントの初期化時のデバッグ部分を修正
try:
    print(f"Debug: Initializing Supabase client with URL: {supabase_url}")
    print(f"Debug: Using key starting with: {supabase_key[:10]}...")
    
    supabase: Client = create_client(
        supabase_url,
        supabase_key
    )
    
    # 接続テストを削除（この部分が問題を引き起こしている）
    # test = supabase.table('projects').select("*").limit(1).execute()
    # print(f"Debug: Connection test result: {test}")
    
    print("Supabase connection established")
except Exception as e:
    print(f"Debug: Supabase initialization error: {str(e)}")
    raise

# SSL証明書の設定を更新
import os
import ssl
import certifi

# 基本的なSSL設定
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['SSL_CERT_FILE'] = certifi.where()

# 一時ファイルのパスを修正
TEMP_DIR = "/tmp"
DOWNLOAD_DIR = f"{TEMP_DIR}/downloads"
SCREENSHOT_DIR = f"{TEMP_DIR}/screenshots"

# ディレクトリの作成
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# YouTube cookiesの設定を改善
def get_youtube_cookies():
    try:
        # Chrome/Chromiumのクッキーを取得
        cookies = browser_cookie3.chrome(domain_name='.youtube.com')
        return cookies
    except:
        try:
            # Firefoxのクッキーを取得
            cookies = browser_cookie3.firefox(domain_name='.youtube.com')
            return cookies
        except:
            return None

# yt-dlpの設定を更新
async def get_yt_dlp_opts():
    try:
        print(f"Debug: Current environment: {os.getenv('VERCEL_ENV', 'unknown')}")
        
        # 共通のオプション
        opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
            'debug': True,
            # loggerはJSON化できないのでデバッグ出力時は除外
            'logger': CustomLogger(),
            # 最新のChrome User-Agent
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }

        # 環境変数からCookieを取得
        cookies_str = os.getenv('YOUTUBE_COOKIES')
        if cookies_str:
            print("Debug: Using environment cookies")
            cookies_path = '/tmp/youtube.com_cookies.txt'
            
            # Netscape形式でCookieファイルを作成
            with open(cookies_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
                f.write("# This is a generated file!  Do not edit.\n\n")
                
                for cookie in cookies_str.split(';'):
                    if '=' in cookie:
                        name, value = cookie.strip().split('=', 1)
                        f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n")
            
            opts['cookies'] = cookies_path
        else:
            print("Debug: No cookies found in environment")

        # デバッグ出力用にloggerを除外したオプションを作成
        debug_opts = opts.copy()
        debug_opts.pop('logger', None)
        print(f"Debug: Final yt-dlp options: {json.dumps(debug_opts, indent=2)}")
        
        return opts
        
    except Exception as e:
        print(f"Debug: Error in get_yt_dlp_opts: {str(e)}")
        print(f"Debug: Error traceback: {traceback.format_exc()}")
        raise

# カスタムロガーの追加
class CustomLogger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            print(f"YT-DLP Debug: {msg}")
    
    def warning(self, msg):
        print(f"YT-DLP Warning: {msg}")
    
    def error(self, msg):
        print(f"YT-DLP Error: {msg}")

def save_to_markdown(video_id: str, url: str, transcription: str, translation: str):
    """結果をMarkdownファイルとして保存する"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/tmp/outputs/{video_id}_{timestamp}.md"  # /tmp に変更
    
    content = f"""# YouTube 文字起こし & 翻訳結果

## 元動画情報
- URL: {url}
- 処理日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 文字起こし結果
{transcription}

## 英訳結果
{translation}
"""
    
    os.makedirs('/tmp/outputs', exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename

def extract_video_id(url: str) -> str:
    """YouTube URLからVideo IDを抽出する"""
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            return info['id']
    except Exception:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

async def upload_to_supabase(file_path: str, content_type: str, bucket: str = 'videos') -> str:
    try:
        file_name = f"{uuid.uuid4()}{os.path.splitext(file_path)[1]}"
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
            
        print(f"Uploading file {file_name} to bucket {bucket}")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        # アップロード処理
        storage = supabase.storage.from_(bucket)
        result = storage.upload(
            path=file_name,
            file=file_data,
            file_options={"contentType": content_type}
        )
        
        if not result:
            raise Exception("Upload failed: No response from storage")
            
        # 公開URLを取得
        file_url = storage.get_public_url(file_name)
        print(f"File uploaded successfully: {file_url}")
        
        return file_url
        
    except Exception as e:
        print(f"Upload error details: {str(e)}")
        print(f"File path: {file_path}")
        print(f"Content type: {content_type}")
        print(f"Bucket: {bucket}")
        raise Exception(f"Supabaseへのアップロードに失敗しました: {str(e)}")

# 動画の長さをチェック関数を修正
async def check_video_duration(youtube_url: str) -> Dict:
    try:
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'cookies_from_browser': 'chrome'  # ここにも追加
        }) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            if not info:
                raise Exception("動画情報の取得に失敗しました")
                
            duration = info.get('duration', 0)
            
            return {
                'is_valid': duration <= 180,
                'duration': duration,
                'id': info.get('id'),
                'thumbnail': info.get('thumbnail')
            }
    except Exception as e:
        print(f"Error checking video duration: {str(e)}")
        raise Exception(f"動画情報の取得に失敗しました: {str(e)}")

# プロジェクト保存関数の修正
async def save_project_to_db(video_url: str, video_path: str = None, screenshots: list = None, status: str = 'pending', error_message: str = None, metadata: dict = None):
    try:
        # statusの値を検証
        valid_statuses = {'pending', 'processing', 'completed', 'error'}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status value. Must be one of: {', '.join(valid_statuses)}")
            
        data = {
            'video_url': video_url,
            'video_path': video_path,
            'screenshots': json.dumps(screenshots or []),
            'status': status,
            'error_message': error_message,
            'metadata': json.dumps(metadata or {}),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"Debug: Attempting to save project with data:")
        print(json.dumps(data, indent=2))
        
        response = supabase.table('projects').insert(data).execute()
        print(f"Debug: Insert response: {response}")
        
        return response.data[0]
    except Exception as e:
        print(f"Debug: Error details: {str(e)}")
        print(f"Debug: Error type: {type(e)}")
        raise

# プロジェクト更新関数の追加
async def update_project_status(project_id: str, status: str, error_message: str = None):
    try:
        data = {
            'status': status,
            'error_message': error_message,
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('projects').update(data).eq('id', project_id).execute()
        return response.data[0]
    except Exception as e:
        print(f"ステータス更新エラー: {str(e)}")

# 動画からスクリーンショットを生成する関数
async def generate_screenshots(video_path: str, num_screenshots: int) -> List[str]:
    try:
        screenshot_urls = []
        for i in range(num_screenshots):
            # スクリーンショットの生成
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"{uuid.uuid4()}.jpg")
            
            # FFmpegコマンドの実行
            timestamp = i * 30  # 30秒間隔でスクリーンショットを生成
            stream = ffmpeg.input(video_path, ss=timestamp)
            stream = ffmpeg.output(stream, screenshot_path, vframes=1)
            ffmpeg.run(stream)
            
            # Supabaseにアップロード
            screenshot_url = await upload_to_supabase(
                screenshot_path,
                'image/jpeg',
                'videos'  # バケット名を明示的に指定
            )
            
            screenshot_urls.append(screenshot_url)
            os.remove(screenshot_path)  # 一時ファイルを削除
            
        return screenshot_urls
        
    except Exception as e:
        print(f"Error generating screenshots: {str(e)}")
        raise Exception(f"スクリーンショットの生成に失敗しました: {str(e)}")

# OpenAI APIによる文字起こしと翻訳を修正
async def transcribe_and_translate(audio_file: str):
    try:
        # Whisper APIによる文字起こし
        print("Starting transcription with Whisper API...")
        with open(audio_file, "rb") as audio:
            # 同期的に実行するように修正
            transcription = openai.audio.transcriptions.create(
                file=audio,
                model="whisper-1",
                language="ja"
            ).text
        print("Transcription completed")

        # GPT-4 Optimized (Mini)による翻訳
        print("Starting translation with GPT-4 Optimized (Mini)...")
        # Chat Completionsの呼び出しを修正
        translation_response = openai.chat.completions.create(  # awaitを削除
            model=env_vars['AI_MODEL'],
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the following Japanese text to English, maintaining the original meaning and nuance:"},
                {"role": "user", "content": transcription}
            ]
        )
        translation = translation_response.choices[0].message.content
        print("Translation completed")

        return transcription, translation

    except Exception as e:
        print(f"API Error: {str(e)}")
        raise Exception(f"文字起こしまたは翻訳に失敗しました: {str(e)}")

# ビデオ情報保存関数を修正
async def save_video_to_db(
    youtube_url: str,
    youtube_id: str,
    video_path: Optional[str] = None,
    transcription: Optional[str] = None,
    translation: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    duration: Optional[int] = None
) -> Dict:
    try:
        # まず既存の動画を検索
        existing_video = supabase.table('videos').select("*").eq('youtube_id', youtube_id).execute()
        
        if existing_video.data:
            # 既存の動画が見つかった場合は更新
            data = {
                'youtube_url': youtube_url,
                'video_path': video_path if video_path else existing_video.data[0]['video_path'],
                'transcription': transcription if transcription else existing_video.data[0]['transcription'],
                'translation': translation if translation else existing_video.data[0]['translation'],
                'thumbnail_url': thumbnail_url if thumbnail_url else existing_video.data[0]['thumbnail_url'],
                'duration': duration if duration else existing_video.data[0]['duration'],
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            response = supabase.table('videos').update(data).eq('youtube_id', youtube_id).execute()
        else:
            # 新規動画の場合は挿入
            data = {
                'youtube_url': youtube_url,
                'youtube_id': youtube_id,
                'video_path': video_path,
                'transcription': transcription,
                'translation': translation,
                'thumbnail_url': thumbnail_url,
                'duration': duration,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            response = supabase.table('videos').insert(data).execute()
        
        return response.data[0]
    except Exception as e:
        print(f"Debug: Video save error: {str(e)}")
        raise Exception(f"ビデオ情報の保存に失敗しました: {str(e)}")

# 処理ログ記録関数
async def log_processing_status(video_id: str, status: str, message: Optional[str] = None):
    try:
        data = {
            'video_id': video_id,
            'status': status,
            'message': message
        }
        
        response = supabase.table('processing_logs').insert(data).execute()
        return response.data[0]
    except Exception as e:
        print(f"処理ログの記録に失敗しました: {str(e)}")

@app.get("/")
async def index(request: Request):
    site_url = os.getenv("NEXT_PUBLIC_SITE_URL", str(request.base_url).rstrip('/'))
    return templates.TemplateResponse("index.html", {
        "request": request,
        "config": {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_ANON_KEY": os.getenv("SUPABASE_KEY"),
            "SITE_URL": site_url
        }
    })

@app.post("/process")
async def process_video(youtube_url: str = Form(...), num_screenshots: int = Form(3)):
    try:
        # YouTube APIで動画情報を取得
        video_info = await get_video_info(youtube_url)
        
        # 動画の長さをチェック（180秒以内）
        if video_info['duration'] > 180:
            raise Exception("動画が180秒を超えています")
            
        # プロジェクトを作成
        project = await save_project_to_db(
            video_url=youtube_url,
            status='pending',
            metadata={
                'requested_screenshots': num_screenshots,
                'title': video_info['title'],
                'channel': video_info['channel_title'],
                'duration': video_info['duration'],
                'thumbnail': video_info['thumbnail']
            }
        )

        try:
            # ステータスを処理中に更新
            await update_project_status(project['id'], 'processing')

            # 動画情報をDBに保存
            video = await save_video_to_db(
                youtube_url=youtube_url,
                youtube_id=video_info['id'],
                thumbnail_url=video_info.get('thumbnail'),
                duration=video_info.get('duration')
            )

            # 処理開始ログを記録
            await log_processing_status(video['id'], 'processing', '処理を開始しました')

            # 動画のダウンロードと保存
            ydl_opts = await get_yt_dlp_opts()
            print(f"Debug: Using yt-dlp options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Debug: Attempting to extract video info...")
                info = ydl.extract_info(youtube_url, download=True)
                if not info:
                    raise Exception("動画情報の取得に失敗しました")
                print(f"Debug: Successfully extracted video info for ID: {info.get('id')}")
                
                # ダウンロードされたファイルのパスを取得
                downloaded_file = os.path.join(DOWNLOAD_DIR, f"{info['id']}.mp4")
                print(f"Debug: Downloaded file path: {downloaded_file}")
                
            # Supabaseに動画をアップロード
            video_path = await upload_to_supabase(
                downloaded_file,
                'video/mp4',
                'videos'
            )

            # ビデオパスを更新
            supabase.table('videos').update({
                'video_path': video_path
            }).eq('id', video['id']).execute()

            # スクリーンショットの生成と保存
            screenshots = await generate_screenshots(downloaded_file, num_screenshots)

            # 文字起こしと翻訳を実行
            transcription, translation = await transcribe_and_translate(downloaded_file)

            # ビデオ情報を更新
            supabase.table('videos').update({
                'transcription': transcription,
                'translation': translation
            }).eq('id', video['id']).execute()

            # プロジェクトを更新（完了状態）
            project = await save_project_to_db(
                video_url=youtube_url,
                video_path=video_path,
                screenshots=screenshots,
                status='completed',
                metadata={
                    'video_id': video['id'],
                    'requested_screenshots': num_screenshots,
                    'duration': video_info.get('duration'),
                    'thumbnail_url': video_info.get('thumbnail')
                }
            )

            # 処理完了ログを記録
            await log_processing_status(video['id'], 'completed', '処理が完了しました')

            # 一時ファイルの削除
            os.remove(downloaded_file)

            return JSONResponse({
                'success': True,
                'project_id': project['id'],
                'video_id': video['id'],
                'video_path': video_path,
                'screenshots': screenshots,
                'transcription': transcription,
                'translation': translation,
                'status': 'completed'
            })

        except Exception as e:
            # エラー発生時の処理
            error_message = str(e)
            await update_project_status(project['id'], 'error', error_message)
            if 'video' in locals():
                await log_processing_status(video['id'], 'error', error_message)
            raise

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse({
            'success': False,
            'error': str(e)
        })

@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        site_url = os.getenv("NEXT_PUBLIC_SITE_URL", str(request.base_url).rstrip('/'))
        
        # 環境に応じたCookieドメインを設定
        cookie_domain = os.getenv("COOKIE_DOMAIN", "localhost")
        
        # セッショントークンの取得と設定
        if "#" in str(request.url):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "config": {
                    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
                    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_KEY"),
                    "SITE_URL": site_url,
                    "COOKIE_DOMAIN": cookie_domain
                }
            })
        
        return RedirectResponse(url=site_url)
        
    except Exception as e:
        print(f"Auth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/debug")
async def auth_debug():
    try:
        # Supabaseの設定を確認
        return {
            "supabase_url": supabase_url[:20] + "...",  # URLの一部のみ表示
            "auth_config": {
                "provider": "google",
                "flow_type": "pkce",
                "redirect_url": "/auth/callback"
            },
            "google_config": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID")[:20] + "..."  # IDの一部のみ表示
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug")
async def debug_info(request: Request):
    return {
        "base_url": str(request.base_url),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "env_vars": {k: v for k, v in os.environ.items() if 'GOOGLE' in k},
        "headers": dict(request.headers)
    }

# アプリケーション起動時にディレクトリを作成
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs('/tmp/outputs', exist_ok=True)

# cookiesファイルの設定
COOKIES_PATH = '/tmp/youtube.com_cookies.txt'

# アプリケーション起動時にcookiesを設定
def setup_cookies():
    try:
        cookies_str = os.getenv('YOUTUBE_COOKIES')
        if cookies_str:
            cookies_path = '/tmp/youtube.com_cookies.txt'
            # Netscape形式でCookieファイルを作成
            with open(cookies_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
                f.write("# This is a generated file!  Do not edit.\n\n")
                
                # 各Cookieを正しい形式で書き込み
                cookies = cookies_str.split(';')
                for cookie in cookies:
                    if '=' in cookie:
                        name, value = cookie.strip().split('=', 1)
                        f.write(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}\n")
            
            print(f"Debug: Cookie file created at: {cookies_path}")
            return True
        else:
            print("Debug: No YOUTUBE_COOKIES environment variable found")
            return False
    except Exception as e:
        print(f"Debug: Cookie setup error: {str(e)}")
        return False

# アプリケーション起動時に実行
if setup_cookies():
    print("Debug: YouTube cookies configured successfully")

# YouTube API設定
YOUTUBE_API_KEY = YOUTUBE_API_KEY

async def get_video_info(video_url: str) -> Dict:
    try:
        video_id = extract_video_id(video_url)
        print(f"Debug: Video ID: {video_id}")
        print(f"Debug: API Key: {YOUTUBE_API_KEY}")  # 開発時のみ
        
        # APIキーの検証
        if not YOUTUBE_API_KEY:
            raise ValueError("YouTube API Key is not set")
            
        # YouTubeクライアントの初期化
        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            print("Debug: YouTube client initialized successfully")
        except Exception as e:
            print(f"Debug: Error initializing YouTube client: {str(e)}")
            raise
            
        # API呼び出し
        try:
            video_response = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()
            print(f"Debug: API Response received: {video_response.keys()}")
        except Exception as e:
            print(f"Debug: API call error: {str(e)}")
            raise
        
        if not video_response['items']:
            raise Exception('Video not found')
            
        video_info = video_response['items'][0]
        print(f"Debug: Retrieved video info: {video_info['snippet']['title']}")
        
        # ISO 8601形式の期間を秒数に変換
        duration = video_info['contentDetails']['duration']
        duration_seconds = parse_duration(duration)
        
        return {
            'id': video_id,
            'title': video_info['snippet']['title'],
            'duration': duration_seconds,
            'thumbnail': video_info['snippet']['thumbnails']['high']['url'],
            'view_count': video_info['statistics']['viewCount'],
            'channel_title': video_info['snippet']['channelTitle'],
            'description': video_info['snippet']['description']
        }
        
    except HttpError as e:
        print(f"YouTube API error: {e.resp.status} {e.content}")
        raise
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        raise

def parse_duration(duration: str) -> int:
    """ISO 8601形式の期間を秒数に変換"""
    import re
    import isodate
    return int(isodate.parse_duration(duration).total_seconds())

async def download_video(video_url: str, video_id: str) -> str:
    try:
        # yt-dlpの設定を更新
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
            'cookiefile': '/tmp/youtube.com_cookies.txt',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Debug: Downloading video...")
            ydl.download([video_url])
            
        output_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
        if not os.path.exists(output_path):
            raise Exception(f"Downloaded file not found: {output_path}")
            
        print(f"Debug: Video downloaded successfully to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    import os

    # 環境変数からホストとポートを取得（デフォルト値付き）
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 3000))
    
    # 開発環境かどうかを確認
    is_dev = os.getenv("VERCEL_ENV") == "development"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=is_dev  # 開発環境の場合のみreloadを有効化
    )