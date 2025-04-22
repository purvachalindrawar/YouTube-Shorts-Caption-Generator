const { exec } = require("child_process");
const fs = require("fs");

function transcribeAudio(audioPath) {
  return new Promise((resolve, reject) => {
    const outputTxt = audioPath.replace(".wav", "_transcript.txt");
    const command = `whisper "${audioPath}" --model base --output_format txt --output_dir "${__dirname}/../subs"`;

    exec(command, (err) => {
      if (err) return reject(err);
      fs.readFile(outputTxt, "utf-8", (err, data) => {
        if (err) return reject(err);
        resolve(data);
      });
    });
  });
}

module.exports = { transcribeAudio };
