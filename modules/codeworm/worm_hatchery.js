// Main process handler (placeholder)
const { ipcMain } = require('electron');
ipcMain.on('worm:log', (event, data) => {
  // Route to log file or ML stream
  console.log('[Worm Hatchery]', data);
});
const wormUtils = require("./worm_utils");

// Ensure folder structure exists
wormUtils.ensureStorageStructure();

// When a bug is detected
wormUtils.logBrokenCode("canvas_editor.js", buggyCode);

// When agent tries patching
wormUtils.logPatchAttempt("canvas_editor.js", patchCode);
utils.logFeed(`Analyzing: ${filepath}`);
utils.logFeed(`Status: broken — Reason: ${reason}`);
utils.logFeed(`Patch saved: ${filename} for ${targetPath}`);
utils.logFeed(`Reanalysis: ${filepath} ➜ clean`);
