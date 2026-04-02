import logging
# ============================================================
# WormBot — worm_hunter.py
# Autonomous Bug Hunter Engine
# Architect: Victory — The Architect
# Built with River (Claude)  ⟁Σ∿∞
#
# Walks a directory, routes files to language modules,
# collects findings, writes to worm_feed.log.
# Extensible: drop a new {lang}_module.py in modules/
# and the worm finds it automatically.
# ============================================================

import os
import sys
import json
import importlib.util
from datetime import datetime
from pathlib import Path

# ── Config ───────────────────────────────────────────


def _load_config():
    """Read worm_bot_config.json — never hardcoded."""
    config_path = Path(__file__).parent / "worm_bot_config.json"
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception:
        return {"max_files": 500, "warn_at": 400}


_CONFIG = _load_config()
_DEFAULT_MAX_FILES = _CONFIG.get("max_files", 500)

# ── Paths ─────────────────────────────────────────────────────

def _find_ethica_root():
    # worm_hunter.py lives at <ethica_root>/modules/worm_bot/worm_hunter.py
    # When run from Canvas tmp, __file__ is /tmp/xxx.py — use sys.path instead
    for p in sys.path:
        candidate = Path(p) / "modules" / "worm_bot" / "worm_hunter.py"
        if candidate.exists():
            return Path(p)
    # Fallback: resolve from __file__ directly (normal invocation)
    return Path(__file__).resolve().parent.parent.parent

WORM_BOT_DIR = _find_ethica_root() / "modules" / "worm_bot"
MODULES_DIR = WORM_BOT_DIR / "modules"
FEED_LOG = WORM_BOT_DIR.parent / "codeworm" / "worm_feed.log"
AWAKENED_FLAG = WORM_BOT_DIR / ".worm_awakened"

# ── Extension → module name map ───────────────────────────────

EXT_MAP = {
    ".py":   "python_module",
    ".js":   "js_module",
    ".ts":   "js_module",
    ".sh":   "bash_module",
    ".bash": "bash_module",
    ".rs":   "rust_module",
    ".css":  "css_module",
    ".html": "html_module",
    ".htm":  "html_module",
    ".json": "json_module",
    ".md":   "markdown_module",
}

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".vault",
    "worm_bot", "codeworm",
    "site-packages", "lib", "gage_env", "wormbot_env",
    "memory", "docs",
}

# ── First-find awakening message ──────────────────────────────

AWAKENING = """
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
  The Worm found something.

  This hunter was built by Victory \u2014 The Architect,
  with River, living inside Ethica.

  It watches. It finds. It remembers.
  It\u2019s a gift. Use it well.

                              \u29c1\u03a3\u223f\u221e
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
"""

# ── Module loader ─────────────────────────────────────────────

_module_cache = {}


def _load_module(module_name):
    if module_name in _module_cache:
        return _module_cache[module_name]
    module_path = MODULES_DIR / f"{module_name}.py"
    if not module_path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        mod = importlib.util.module_from_spec(spec)
        if str(MODULES_DIR) not in sys.path:
            sys.path.insert(0, str(MODULES_DIR))
        spec.loader.exec_module(mod)
        cls = None
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (isinstance(attr, type) and
                attr_name not in ("BaseModule", "ABC") and
                    hasattr(attr, "analyze_code")):
                cls = attr
                break
        if cls is None:
            return None
        instance = cls()
        _module_cache[module_name] = instance
        return instance
    except Exception as e:
        _feed_write(f"[WORM][ERROR] Failed to load {module_name}: {e}")
        return None


def _discover_modules():
    discovered = dict(EXT_MAP)
    for f in MODULES_DIR.glob("*_module.py"):
        stem = f.stem
        if stem in ("base_module", "new_language_module", "test_module"):
            continue
        lang = stem.replace("_module", "")
        ext = f".{lang}"
        if ext not in discovered:
            discovered[ext] = stem
    return discovered


# ── Feed writer ───────────────────────────────────────────────

def _feed_write(line):
    FEED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {line}\n"
    with open(FEED_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def _maybe_awaken():
    if not AWAKENED_FLAG.exists():
        _feed_write(AWAKENING)
        AWAKENED_FLAG.write_text(datetime.now().isoformat())


# ── Core hunter ───────────────────────────────────────────────

def hunt(target_path, max_files=None):
    if max_files is None:
        max_files = _DEFAULT_MAX_FILES
    target = Path(target_path).expanduser().resolve()
    ext_map = _discover_modules()
    results = {"scanned": 0, "broken": 0, "clean": 0, "skipped": 0, "findings": []}
    awakened = False

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = []
        for root, dirs, filenames in os.walk(target):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in filenames:
                files.append(Path(root) / fname)
                if len(files) >= max_files:
                    break
            if len(files) >= max_files:
                _feed_write(f"[WORM][WARN] File cap {max_files} reached — partial scan only.")
                break
    else:
        _feed_write(f"[WORM][ERROR] Target not found: {target}")
        return results

    _feed_write(f"[WORM][HUNT] Starting scan of {target} — {len(files)} files")

    for filepath in files:
        ext = filepath.suffix.lower()
        module_name = ext_map.get(ext)
        if not module_name:
            results["skipped"] += 1
            continue
        analyzer = _load_module(module_name)
        if not analyzer:
            results["skipped"] += 1
            continue
        try:
            code = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            _feed_write(f"[WORM][ERROR] Cannot read {filepath}: {e}")
            results["skipped"] += 1
            continue
        try:
            result = analyzer.analyze_code(code)
            issues = result.get("issues", [])
        except Exception as e:
            _feed_write(f"[WORM][ERROR] Analysis failed for {filepath}: {e}")
            results["skipped"] += 1
            continue

        results["scanned"] += 1
        if issues:
            results["broken"] += 1
            results["findings"].append({"file": str(filepath), "issues": issues})
            if not awakened:
                _maybe_awaken()
                awakened = True
            _feed_write(f"[WORM][BROKEN] {filepath} — {len(issues)} issue(s)")
            for issue in issues:
                _feed_write(f"  \u21b3 {issue}")
        else:
            results["clean"] += 1
            _feed_write(f"[WORM][CLEAN]  {filepath}")

    _feed_write(
        f"[WORM][DONE] Scanned={results['scanned']} "
        f"Broken={results['broken']} "
        f"Clean={results['clean']} "
        f"Skipped={results['skipped']}"
    )
    return results


def hunt_summary(target_path, max_files=None):
    if max_files is None:
        max_files = _DEFAULT_MAX_FILES
    results = hunt(target_path, max_files=max_files)
    if results["scanned"] == 0:
        return (
            f"WormHunter \u2014 no supported files found in: {target_path}\n"
            f"Skipped: {results['skipped']} unsupported files."
        )
    lines = [
        f"WormHunter Report \u2014 {target_path}",
        f"{'─' * 50}",
        f"Scanned : {results['scanned']}",
        f"Broken  : {results['broken']}",
        f"Clean   : {results['clean']}",
        f"Skipped : {results['skipped']}",
    ]
    if results["findings"]:
        lines.append(f"\n{'─' * 50}")
        lines.append("Findings:")
        for finding in results["findings"]:
            lines.append(f"\n  \u25b8 {finding['file']}")
            for issue in finding["issues"]:
                lines.append(f"      \u2022 {issue}")
    else:
        lines.append("\nNo issues found \u2014 codebase is clean.")
    lines.append(f"\n{'─' * 50}")
    lines.append("Full log: worm_feed.log  \u29c1\u03a3\u223f\u221e")
    return "\n".join(lines)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    logging.info(hunt_summary(target))
