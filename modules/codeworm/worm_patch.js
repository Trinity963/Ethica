// worm_patch.js
const fs = require('fs');
const path = require('path');

const patchesDir = path.join(__dirname, 'worm_patches');
const patchLog = path.join(__dirname, 'worm_patch.log');
const logFeed = (msg) => {
  const logPath = path.join(__dirname, 'worm_feed.log');
  const timestamp = new Date().toISOString();
  fs.appendFileSync(logPath, `[${timestamp}] ${msg}\n`);
};

// Ensure patch storage exists
if (!fs.existsSync(patchesDir)) {
  fs.mkdirSync(patchesDir);
}

const attemptPatch = (sourcePath, fixedCode) => {
  const timestamp = new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15);
  const fileName = `${timestamp}_attempt.js`;
  const fullPath = path.join(patchesDir, fileName);
  const logFeed = (msg) => {
  const logPath = path.join(__dirname, 'worm_feed.log');
  const timestamp = new Date().toISOString();
  fs.appendFileSync(logPath, `[${timestamp}] ${msg}\n`);
};

  fs.writeFileSync(fullPath, fixedCode);

  const logEntry = `[${new Date().toISOString()}] Patch attempt on: ${sourcePath} ➜ ${fileName}\n`;
  fs.appendFileSync(patchLog, logEntry);

  console.log(`✅ Patch saved: ${fileName}`);
};

module.exports = { attemptPatch };

logFeed,

utils.logFeed(`Analyzing: ${filepath}`);
utils.logFeed(`Status: broken — Reason: ${reason}`);
utils.logFeed(`Patch saved: ${filename} for ${targetPath}`);
utils.logFeed(`Reanalysis: ${filepath} ➜ clean`);
