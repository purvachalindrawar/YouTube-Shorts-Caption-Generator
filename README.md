# 🎬 YouTube Shorts Caption Generator

This project allows you to generate short video clips from any YouTube link and overlay them with AI-transcribed captions — just like Instagram Reels or YouTube Shorts!

## ⚙️ Features
- ⏱ Extract specific video clips using timestamps.
- 🧠 Transcribe audio using OpenAI Whisper.
- 🎞️ Automatically generate and style captions (.ass format).
- 🔥 Burn captions directly into the video using FFmpeg.
- 🚀 Interactive UI built with Streamlit.

## 🧰 Tech Stack
- Python
- Streamlit
- yt-dlp (YouTube Downloader)
- FFmpeg (Video Processing)
- Whisper (Audio Transcription)


## 🛠️ Setup Instructions

1. **Clone the repository**  
```bash
git clone https://github.com/yourusername/yt-shorts-caption-generator.git
cd yt-shorts-caption-generator

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

ffmpeg -version

streamlit run app.py

```
## Sample Use Case 
### Input : YouTube URL and timestamps (e.g., 00:30 to 00:40)
### Output : A short video with stylized embedded captions, downloadable
