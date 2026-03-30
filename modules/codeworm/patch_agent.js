const fs = require('fs');
const path = require('path');
const utils = require('./worm_utils');
const { analyzeFile } = require('./internal_debug/codeworm/worm_listener');

utils.ensureDirsExist();

function attemptPatch(codeStr) {
  // Placeholder logic: real patching would involve AST / LLM logic
  let patched = codeStr;

  if (codeStr.includes('throw')) {
    patched = codeStr.replace(/throw\s+.*?;/g, '// ⟁patch# throw removed');
  }

  if (codeStr.includes('undefined')) {
    patched = patched.replace(/undefined/g, 'null // ⟁patch# undefined->null');
  }

  const changesMade = patched !== codeStr;
  return {
    success: changesMade,
    patchedCode: patched,
    reason: changesMade ? 'Basic patch applied' : 'No patch needed',
  };
}

function patchAndStore(filepath) {
  const absPath = path.resolve(filepath);
  if (!fs.existsSync(absPath)) {
    console.error(`❌ File not found: ${absPath}`);
    return;
  }

  const originalCode = fs.readFileSync(absPath, 'utf-8');
  const result = attemptPatch(originalCode);

  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, '');
  const patchName = `${stamp}_attempt.js`;

  if (result.success) {
    utils.storePatch(patchName, result.patchedCode);
  }

  utils.logFeed({
    file: filepath,
    outcome: result.reason,
    patched: result.success,
    timestamp: new Date().toISOString(),
  });

  return result;
}

module.exports = {
  attemptPatch,
  patchAndStore,
};
