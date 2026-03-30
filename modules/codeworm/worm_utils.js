#!/usr/bin/env node


// worm_utils.js
const fs = require('fs');
const path = require('path');

const storageBase = path.resolve(__dirname, 'storage');

const dirs = {
  broken_code: 'broken_code',
  patch_attempts: 'patch_attempts',
  false_positives: 'false_positives',
  meta_traces: 'meta_traces',
};

function ensureDirsExist() {
  Object.values(dirs).forEach(dir => {
    const fullPath = path.join(storageBase, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
    }
  });
}
const logFeed = (msg) => {
  const logPath = path.join(__dirname, 'worm_feed.log');
  const timestamp = new Date().toISOString();
  fs.appendFileSync(logPath, `[${timestamp}] ${msg}\n`);
};


function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function storeTo(dirKey, fileName, content) {
  if (!dirs[dirKey]) throw new Error(`Invalid storage path: ${dirKey}`);
  const dirPath = path.join(storageBase, dirs[dirKey]);
  const fullPath = path.join(dirPath, `${timestamp()}_${fileName}`);
  fs.writeFileSync(fullPath, content, 'utf-8');
}

module.exports = {
  ensureDirsExist,
  storeBroken: (name, content) => storeTo('broken_code', name, content),
  storePatch: (name, content) => storeTo('patch_attempts', name, content),
  storeFalsePositive: (name, content) => storeTo('false_positives', name, content),
  storeMeta: (name, content) => storeTo('meta_traces', name, content),
  logFeed,
};

