const socket = io();

function processVideo() {
  const url = document.getElementById("url").value;
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  document.getElementById("status").innerText = "Starting...";
  document.getElementById("transcript").value = "";
  document.getElementById("result").style.display = "none";
  document.getElementById("downloadBtn").style.display = "none";

  socket.emit("process-video", { url, start, end });
}

socket.on("status", (msg) => {
  document.getElementById("status").innerText = `Status: ${msg}`;
});

socket.on("transcript", (text) => {
  document.getElementById("transcript").value = text;
});

socket.on("done", ({ video, transcript }) => {
  const resultVideo = document.getElementById("result");
  resultVideo.src = video;
  resultVideo.style.display = "block";

  const downloadBtn = document.getElementById("downloadBtn");
  downloadBtn.href = video;
  downloadBtn.style.display = "block";

  document.getElementById("status").innerText = "✅ All Done!";
});
