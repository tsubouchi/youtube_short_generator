import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200

def test_process_video_invalid_url():
    response = client.post(
        "/process",
        data={
            "youtube_url": "invalid_url",
            "num_screenshots": 3
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == False
    assert "error" in response.json()

def test_process_video_long_video():
    # 3分以上の動画のURLを使用
    response = client.post(
        "/process",
        data={
            "youtube_url": "https://www.youtube.com/watch?v=long_video_id",
            "num_screenshots": 3
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == False
    assert "180秒を超えています" in response.json()["error"]

def test_process_video_success():
    # 3分未満のショート動画のURLを使用
    response = client.post(
        "/process",
        data={
            "youtube_url": "https://www.youtube.com/watch?v=short_video_id",
            "num_screenshots": 3
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "project_id" in response.json()
    assert "video_id" in response.json()
    assert "screenshots" in response.json()
    assert "transcription" in response.json()
    assert "translation" in response.json() 