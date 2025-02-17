from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import yt_dlp
import whisper
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

# 環境変数の読み込み
load_dotenv()

app = FastAPI()

# テンプレートの設定
templates = Jinja2Templates(directory="templates")

# OpenAI APIキーの設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# yt-dlpの設定を変更
ydl_opts = {
    'format': 'best',  # 最高品質の動画をダウンロード
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'keepvideo': True  # 動画ファイルを保持
}

# Whisperモデルの読み込み
model = whisper.load_model("base")

def save_to_markdown(video_id: str, url: str, transcription: str, translation: str):
    """結果をMarkdownファイルとして保存する"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/{video_id}_{timestamp}.md"
    
    content = f"""# YouTube 文字起こし & 翻訳結果

## 元動画情報
- URL: {url}
- 処理日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 文字起こし結果
{transcription}

## 英訳結果
{translation}
"""
    
    os.makedirs('outputs', exist_ok=True)
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

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process")
async def process_video(youtube_url: str = Form(...)):
    try:
        video_id = extract_video_id(youtube_url)
        
        # YouTubeからの音声ダウンロード
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            audio_file = f"downloads/{info['id']}.mp3"

        # Whisperによる文字起こし
        result = model.transcribe(audio_file)
        transcription = result["text"]

        # OpenAI APIによる英訳
        response = openai.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "Translate the following Japanese text to English:"},
                {"role": "user", "content": transcription}
            ]
        )
        translation = response.choices[0].message.content

        # 結果をMarkdownファイルとして保存
        md_file = save_to_markdown(video_id, youtube_url, transcription, translation)

        # 音声ファイルのみを削除（動画は保持）
        os.remove(audio_file)  # MP3ファイルのみ削除

        return JSONResponse({
            'success': True,
            'transcription': transcription,
            'translation': translation,
            'markdown_file': md_file
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        })

# アプリケーション起動時にディレクトリを作成
os.makedirs('downloads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)