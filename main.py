import os
import uuid
import requests
import base64
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import aiofiles

load_dotenv()

app = FastAPI(title="Telugu TTS Generator")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

UPLOAD_DIR = "uploads/texts"
OUTPUT_DIR = "outputs/audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TextFile(BaseModel):
    filename: str
    content: str

class AudioFile(BaseModel):
    filename: str

class GenerateAudioRequest(BaseModel):
    text_filename: str
    speaker: str = "anushka" # Default speaker updated to a valid one

@app.post("/texts/upload", response_model=TextFile)
async def upload_text(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)
        
    return {"filename": file.filename, "content": content.decode("utf-8", errors="ignore")}

@app.get("/texts", response_model=List[str])
async def list_texts():
    return os.listdir(UPLOAD_DIR)

@app.post("/audio/generate", response_model=AudioFile)
async def generate_audio(request: GenerateAudioRequest):
    text_path = os.path.join(UPLOAD_DIR, request.text_filename)
    if not os.path.exists(text_path):
        raise HTTPException(status_code=404, detail="Text file not found")
    
    async with aiofiles.open(text_path, "r", encoding="utf-8") as f:
        text_content = await f.read()
    
    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Text file is empty")

    if not SARVAM_API_KEY:
        raise HTTPException(status_code=500, detail="Sarvam API Key not configured")

    payload = {
        "inputs": [text_content],
        "target_language_code": "te-IN",
        "speaker": request.speaker,
        "pitch": 0,
        "pace": 1.0,
        "loudness": 1.5,
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": "bulbul:v2" # Updated to a valid model
    }
    
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(SARVAM_TTS_URL, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Sarvam API Error: {response.text}")
    
    try:
        data = response.json()
        audio_base64 = data["audios"][0]
        audio_content = base64.b64decode(audio_base64)
    except (KeyError, IndexError, Exception) as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Sarvam API response: {str(e)}")

    audio_filename = f"{os.path.splitext(request.text_filename)[0]}_{uuid.uuid4().hex[:8]}.mp3"
    audio_path = os.path.join(OUTPUT_DIR, audio_filename)
    
    async with aiofiles.open(audio_path, "wb") as f:
        await f.write(audio_content)
        
    return {"filename": audio_filename}


@app.get("/audio", response_model=List[str])
async def list_audio():
    return os.listdir(OUTPUT_DIR)

@app.get("/audio/{filename}")
async def download_audio(filename: str):
    audio_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
