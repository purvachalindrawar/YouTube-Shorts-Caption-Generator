import streamlit as st
import yt_dlp
import ffmpeg
import whisper
import os
import uuid

# Create folders if they don't exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("subs", exist_ok=True)

# ========== Download YouTube Video ==========
def download_youtube_clip(url, start_time, end_time):
    unique_id = str(uuid.uuid4())
    output_path = f"downloads/video_{unique_id}_clip.mp4"

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'download_sections': {
            '*': [f"{start_time}-{end_time}"]
        },
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path


# ========== Time Conversion ==========
def convert_to_seconds(time_str):
    parts = list(map(int, time_str.strip().split(":")))
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    elif len(parts) == 2:
        return parts[0]*60 + parts[1]
    else:
        return parts[0]

# ========== Strip Video ==========
def strip_video(input_path, start_time, end_time):
    output_path = input_path.replace(".mp4", "_stripped.mp4")
    (
        ffmpeg
        .input(input_path, ss=start_time, to=end_time)
        .output(output_path, codec="copy")
        .run(overwrite_output=True)
    )
    return output_path

# ========== Extract Audio ==========
def extract_audio(video_path):
    audio_path = video_path.replace(".mp4", ".wav")
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run()
    )
    return audio_path

# ========== Transcribe Audio using Whisper ==========
def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['text']

# ========== Split Transcript into Short Lines ==========
def split_transcript(text, max_len=40):
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

# ========== Generate .ass Subtitle File ==========
def generate_ass_subs(transcript, output_path="subs/subtitles.ass"):
    lines = split_transcript(transcript)
    duration_per_line = 2  # seconds

    header = """
[Script Info]
Title: Captions
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF,&H00000000,-1,0,1,2,1,2,20,20,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    body = ""
    for i, line in enumerate(lines):
        start = i * duration_per_line
        end = start + duration_per_line
        start_time = "{:02d}:{:02d}:{:02d}.00".format(start // 3600, (start % 3600) // 60, start % 60)
        end_time = "{:02d}:{:02d}:{:02d}.00".format(end // 3600, (end % 3600) // 60, end % 60)
        body += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + body)

    return output_path

# ========== Burn Subtitles into Video ==========
def burn_subtitles(video_path, subtitle_path, output_path="output/final_captioned_video.mp4"):
    os.makedirs("output", exist_ok=True)
    (
        ffmpeg
        .input(video_path)
        .output(output_path, vf=f"subtitles='{subtitle_path}'", vcodec="libx264", acodec="aac")
        .overwrite_output()
        .run()
    )
    return output_path


# ========== Streamlit UI ==========
st.set_page_config(page_title="Shorts Generator", layout="centered")
st.title("🎬 YouTube Shorts Generator (Fast + Clean)")
st.caption("Enter a YouTube link and generate stylized captions with FFmpeg.")

url = st.text_input("📺 Enter YouTube Video URL")
start_time_str = st.text_input("⏱️ Start Time (hh:mm:ss or mm:ss)", "00:00")
end_time_str = st.text_input("⏱️ End Time (hh:mm:ss or mm:ss)", "00:10")

if st.button("🚀 Process Video"):
    if not url:
        st.error("❌ Please enter a YouTube video link.")
    else:
        with st.spinner("⏳ Processing..."):
            try:
                stripped_video_path = download_youtube_clip(url, start_time_str, end_time_str)

                # Transcribe audio
                audio_path = extract_audio(stripped_video_path)
                transcript = transcribe_audio(audio_path)

                # Show transcript
                st.video(stripped_video_path)
                st.subheader("📝 Transcript")
                st.text_area("Transcript Output", transcript, height=300)

                # Generate .ass file & burn subtitles
                subtitle_file = generate_ass_subs(transcript)
                final_output_path = burn_subtitles(stripped_video_path, subtitle_file)

                st.subheader("🎞️ Captioned Final Video")
                st.video(final_output_path)
                st.download_button("📥 Download Captioned Video", open(final_output_path, 'rb'), file_name="captioned_video.mp4")

            except Exception as e:
                st.error(f"❌ Error: {e}")


