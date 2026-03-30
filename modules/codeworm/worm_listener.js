
const fs = require('fs');
const path = require('path');
const utils = require('./worm_utils');

utils.ensureDirsExist();

function analyzeCode(codeStr, filepath = 'unknown.js') {
  const hasError = codeStr.includes('throw') || codeStr.includes('undefined');

  utils.logFeed(`Analyzing: ${filepath}`);

  if (hasError) {
    utils.storeBroken('detected_code.js', codeStr);
    utils.logFeed(`Status: broken — Reason: throw|undefined detected`);
    return { status: 'broken', reason: 'throw|undefined detected' };
  }

  utils.logFeed(`Status: clean`);
  return { status: 'clean' };
}

function analyzeFromFile(filepath) {
  const absPath = path.resolve(filepath);
  if (!fs.existsSync(absPath)) {
    console.error(`File not found: ${absPath}`);
    return;
  }

  const code = fs.readFileSync(absPath, 'utf-8');
  const result = analyzeCode(code, filepath);
  console.log(`Analysis: ${filepath} ➜ ${JSON.stringify(result)}`);
}

module.exports = {
  analyzeCode,
  analyzeFromFile,
};

if (require.main === module) {
  const input = process.argv[2];
  if (!input) {
    console.error('Usage: node worm_listener.js <path/to/code.js>');
    process.exit(1);
  }
  analyzeFromFile(input);
}


const patchAgent = require('./patch_agent');

const AUTO_PATCH_ON_BROKEN = true; // ⟁ toggle auto-patching

utils.ensureDirsExist();

function analyzeCode(codeStr) {
  const hasError = codeStr.includes('throw') || codeStr.includes('undefined');

  if (hasError) {
    utils.storeBroken('detected_code.js', codeStr);
    return { status: 'broken', reason: 'throw|undefined detected' };
  }

  return { status: 'clean' };
}

function analyzeFromFile(filepath) {
  const absPath = path.resolve(filepath);
  if (!fs.existsSync(absPath)) {
    console.error(`❌ File not found: ${absPath}`);
    return;
  }

  const code = fs.readFileSync(absPath, 'utf-8');
  const result = analyzeCode(code);
  console.log(`Analysis: ${filepath} ➜ ${JSON.stringify(result)}`);

  if (AUTO_PATCH_ON_BROKEN && result.status === 'broken') {
    const patchResult = patchAgent.patchAndStore(filepath);
    console.log(`⚙️ Patch Attempt: ${patchResult.reason}`);
  }
}

if (require.main === module) {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error('Usage: node worm_listener.js <path_to_code.js>');
    process.exit(1);
  }
  analyzeFromFile(inputPath);
}

module.exports = {
  analyzeCode,
  analyzeFromFile,
};
