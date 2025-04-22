import os
import uuid
import requests
import subprocess
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}

os.makedirs("downloads", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("subs", exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    start_time: str
    end_time: str

@app.post("/process")
def process_video(req: VideoRequest):
    try:
        clip_path = stream_clip(req.url, req.start_time, req.end_time)
        audio_path = extract_audio(clip_path)
        transcript = transcribe_audio(audio_path)
        subs_path = generate_subtitles(transcript)
        final_video = burn_captions(clip_path, subs_path)

        return {
            "message": "Success",
            "transcript": transcript,
            "video_path": final_video
        }
    except Exception as e:
        return {"error": str(e)}


def stream_clip(url, start_time, end_time):
    uid = str(uuid.uuid4())
    clip_path = f"downloads/{uid}_clip.mp4"
    stream_url = subprocess.check_output(["yt-dlp", "-g", url]).decode().split("\n")[0]

    duration = time_diff(start_time, end_time)
    subprocess.run([
        "ffmpeg", "-ss", start_time, "-i", stream_url,
        "-t", str(duration), "-c", "copy", clip_path, "-y"
    ], check=True)
    return clip_path


def time_diff(start, end):
    def to_sec(t):
        parts = list(map(int, t.split(":")))
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            return parts[0]*60 + parts[1]
        return int(parts[0])
    return to_sec(end) - to_sec(start)


def extract_audio(video_path):
    audio_path = video_path.replace(".mp4", ".wav")
    subprocess.run([
        "ffmpeg", "-i", video_path, "-ar", "16000",
        "-ac", "1", "-f", "wav", audio_path, "-y"
    ], check=True)
    return audio_path


def transcribe_audio(audio_path):
    with open(audio_path, 'rb') as f:
        upload = requests.post("https://api.assemblyai.com/v2/upload", headers=HEADERS, files={"file": f})
    audio_url = upload.json()["upload_url"]

    transcript_req = requests.post("https://api.assemblyai.com/v2/transcript",
        headers=HEADERS, json={"audio_url": audio_url})
    transcript_id = transcript_req.json()["id"]

    status = "queued"
    while status not in ["completed", "error"]:
        res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=HEADERS).json()
        status = res["status"]
        if status == "completed":
            return res["text"]
        elif status == "error":
            raise Exception(res["error"])


def generate_subtitles(text, output_path="subs/captions.ass"):
    lines = split_transcript(text)
    duration = 2
    header = """
[Script Info]
Title: Styled Captions
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BoldColor,Arial,48,&H00FFFF00,&H00000000,-1,0,1,3,1,2,30,30,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = ""
    for i, line in enumerate(lines):
        start = seconds_to_ass(i * duration)
        end = seconds_to_ass((i + 1) * duration)
        events += f"Dialogue: 0,{start},{end},BoldColor,,0,0,0,,{{\\an8}}{line}\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + events)
    return output_path


def split_transcript(text, max_len=50):
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) <= max_len:
            line += word + " "
        else:
            lines.append(line.strip())
            line = word + " "
    lines.append(line.strip())
    return lines


def seconds_to_ass(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{int(h):02}:{int(m):02}:{int(s):02}.00"


def burn_captions(video_path, subs_path):
    out_path = "output/final_captioned.mp4"
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"subtitles='{subs_path}'",
        "-c:v", "libx264", "-c:a", "aac",
        out_path, "-y"
    ], check=True)
    return out_path
