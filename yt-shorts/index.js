// index.js - Node.js Backend with Full Logging and Audio File Fix

const express = require("express");
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs");
const { Server } = require("socket.io");
const http = require("http");
const ffmpeg = require("fluent-ffmpeg");
const { generateASSFile } = require("./helpers/subtitle");
const { transcribeAudio } = require("./helpers/whisper");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static("public"));

const DOWNLOAD_DIR = path.join(__dirname, "downloads");
const OUTPUT_DIR = path.join(__dirname, "output");
const SUB_DIR = path.join(__dirname, "subs");

fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.mkdirSync(SUB_DIR, { recursive: true });

io.on("connection", (socket) => {
  socket.on("process-video", async ({ url, start, end }) => {
    const clipName = `clip_${Date.now()}`;
    const outputPath = path.join(DOWNLOAD_DIR, `${clipName}.mp4`);

    const section = `*${start}-${end}`;
    const command = `yt-dlp --download-sections \"${section}\" -f \"mp4\" -o \"${outputPath}\" \"${url}\"`;
    socket.emit("status", "📥 Downloading video...");
    console.log(`📥 yt-dlp command: ${command}`);

    exec(command, async (err) => {
      if (err) {
        console.error("❌ Download failed:", err);
        return socket.emit("error", `Download failed: ${err}`);
      }

      console.log("✅ Video downloaded successfully!");
      const strippedVideo = outputPath.replace(".mp4", "_stripped.mp4");

      socket.emit("status", "✂️ Stripping video...");
      console.log("✂️ Starting FFmpeg strip...");

      ffmpeg(outputPath)
        .setStartTime(start)
        .setDuration(getDuration(start, end))
        .output(strippedVideo)
        .on("end", async () => {
          console.log("✂️ Strip complete! Output:", strippedVideo);
          const audioPath = path.resolve(strippedVideo.replace(".mp4", "_audio.wav"));

          fs.mkdirSync(path.dirname(audioPath), { recursive: true });
          console.log("🎯 Target audio path:", audioPath);

          socket.emit("status", "🔊 Extracting audio...");
          console.log("🔊 Starting audio extraction...");

          ffmpeg(strippedVideo)
            .outputOptions([
              "-acodec pcm_s16le",
              "-ac 1",
              "-ar 16000"
            ])
            .format("wav")
            .save(audioPath)
            .on("end", async () => {
              console.log("🔊 Audio extraction complete! Path:", audioPath);
              socket.emit("status", "📝 Transcribing audio...");
              const transcript = await transcribeAudio(audioPath);

              console.log("📝 Transcription result:", transcript.slice(0, 200), "...");
              socket.emit("transcript", transcript);

              const assFile = path.join(SUB_DIR, `${clipName}.ass`);
              generateASSFile(transcript, assFile);
              console.log("🧾 Subtitle file generated:", assFile);

              socket.emit("status", "🔥 Burning captions...");
              const finalVideo = path.join(OUTPUT_DIR, `${clipName}_final.mp4`);

              ffmpeg(strippedVideo)
                .videoFilters(`subtitles=${assFile}`)
                .output(finalVideo)
                .on("end", () => {
                  console.log("🔥 Final video created:", finalVideo);
                  socket.emit("done", {
                    video: `/output/${path.basename(finalVideo)}`,
                    transcript,
                  });
                })
                .on("error", (e) => {
                  console.error("❌ Error during burning captions:", e.message);
                  socket.emit("error", e.message);
                })
                .run();
            })
            .on("error", (e) => {
              console.error("❌ Error during audio extraction:", e.message);
              socket.emit("error", e.message);
            });
        })
        .on("error", (e) => {
          console.error("❌ Error during stripping video:", e.message);
          socket.emit("error", e.message);
        })
        .run();
    });
  });
});

function getDuration(start, end) {
  const s = toSeconds(start);
  const e = toSeconds(end);
  return e - s;
}

function toSeconds(time) {
  const parts = time.split(":").map(Number);
  if (parts.length === 3)
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return parts[0];
}

server.listen(3002, () => console.log("🚀 Server running on http://localhost:3002"));