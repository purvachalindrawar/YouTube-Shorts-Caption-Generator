const fs = require("fs");

function splitTranscript(text, maxLen = 40) {
  const words = text.split(" ");
  const lines = [];
  let line = "";

  for (let word of words) {
    if ((line + word).length <= maxLen) {
      line += word + " ";
    } else {
      lines.push(line.trim());
      line = word + " ";
    }
  }
  lines.push(line.trim());
  return lines;
}

function generateASSFile(transcript, filePath) {
  const lines = splitTranscript(transcript);
  const durationPerLine = 2;

  const header = `
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
`;

  let body = "";
  lines.forEach((line, i) => {
    const start = i * durationPerLine;
    const end = start + durationPerLine;
    const startStr = new Date(start * 1000).toISOString().substr(11, 8) + ".00";
    const endStr = new Date(end * 1000).toISOString().substr(11, 8) + ".00";
    body += `Dialogue: 0,${startStr},${endStr},Default,,0,0,0,,${line}\n`;
  });

  fs.writeFileSync(filePath, header + body, "utf-8");
}

module.exports = { generateASSFile };
