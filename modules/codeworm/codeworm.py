# ============================================================
# Ethica Module — codeworm.py
# CodeWorm Python Bridge
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Bridges Ethica's Python world to CodeWorm's JavaScript world.
# Ethica reads the feed, checks status, triggers analysis,
# reads broken code archives.
#
# CodeWorm watches. Ethica thinks. V decides.
# ============================================================

import os
import json
import subprocess
import re
from datetime import datetime


# ── Paths ─────────────────────────────────────────────────────

MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
FEED_LOG     = os.path.join(MODULE_DIR, "worm_feed.log")
PATCH_LOG    = os.path.join(MODULE_DIR, "worm_patch.log")
BROKEN_DIR   = os.path.join(MODULE_DIR, "storage", "broken_code")
PATCHES_DIR  = os.path.join(MODULE_DIR, "worm_patches")
LISTENER_JS  = os.path.join(MODULE_DIR, "worm_listener.js")
CONFIG_FILE  = os.path.join(MODULE_DIR, "worm_config.json")


# ── Tool: worm_read_feed ──────────────────────────────────────

def worm_read_feed(input_str):
    """
    Read the CodeWorm feed log.
    Input: "last N" or "all" or empty (defaults to last 20)
    """
    if not os.path.exists(FEED_LOG):
        return "CodeWorm feed is empty — no activity recorded yet."

    try:
        with open(FEED_LOG, "r", encoding="utf-8") as f:
            lines = [l.rstrip() for l in f.readlines() if l.strip()]
    except Exception as e:
        return f"Could not read feed: {e}"

    if not lines:
        return "CodeWorm feed is empty."

    # Parse how many lines to return
    n = 20
    inp = input_str.strip().lower()
    if inp == "all":
        n = len(lines)
    else:
        match = re.search(r'\d+', inp)
        if match:
            n = int(match.group())

    recent = lines[-n:]

    # Parse and summarize
    broken_count = sum(1 for l in recent if "broken" in l.lower())
    clean_count  = sum(1 for l in recent if "clean" in l.lower())
    patch_count  = sum(1 for l in recent if "patch" in l.lower())

    summary = (
        f"CodeWorm Feed — last {len(recent)} entries\n"
        f"Broken: {broken_count}  Clean: {clean_count}  Patches: {patch_count}\n"
        f"{'─' * 40}\n"
    )
    return summary + "\n".join(recent)


# ── Tool: worm_analyze ────────────────────────────────────────

def worm_analyze(input_str):
    """
    Run CodeWorm listener on a specific JS file.
    Input: file path
    """
    filepath = input_str.strip()

    if not filepath:
        return "No file path provided. Usage: [TOOL:worm_analyze: /path/to/file.js]"

    if not os.path.exists(filepath):
        return f"File not found: {filepath}"

    if not os.path.exists(LISTENER_JS):
        return f"CodeWorm listener not found at: {LISTENER_JS}"

    # Check if node is available
    node_check = subprocess.run(
        ["which", "node"],
        capture_output=True, text=True
    )
    if node_check.returncode != 0:
        return "Node.js not found — CodeWorm requires Node.js to run worm_listener.js"

    try:
        result = subprocess.run(
            ["node", LISTENER_JS, filepath],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=MODULE_DIR
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()

        if result.returncode != 0:
            return f"CodeWorm analysis failed:\n{errors or output}"

        return output or f"Analysis complete for: {filepath}"

    except subprocess.TimeoutExpired:
        return f"CodeWorm timed out analyzing: {filepath}"
    except Exception as e:
        return f"CodeWorm error: {e}"


# ── Tool: worm_status ─────────────────────────────────────────

def worm_status(input_str):
    """
    Get full CodeWorm status summary.
    """
    lines = []

    # Config
    config = _read_json(CONFIG_FILE)
    if config:
        enabled  = config.get("enabled", False)
        log_lvl  = config.get("logLevel", "unknown")
        auto     = config.get("agentHook", False)
        lines.append(f"CodeWorm Status")
        lines.append(f"  Enabled:     {'Yes' if enabled else 'No'}")
        lines.append(f"  Log level:   {log_lvl}")
        lines.append(f"  Agent hook:  {'Active' if auto else 'Inactive'}")
    else:
        lines.append("CodeWorm Status — config not found")

    lines.append("")

    # Broken code archive
    broken_files = _list_dir(BROKEN_DIR)
    lines.append(f"Broken code archived: {len(broken_files)} file(s)")
    if broken_files:
        latest = sorted(broken_files)[-1]
        lines.append(f"  Latest: {latest}")

    # Patch attempts
    patch_files = _list_dir(PATCHES_DIR)
    lines.append(f"Patch attempts:       {len(patch_files)} file(s)")

    # Feed log
    if os.path.exists(FEED_LOG):
        with open(FEED_LOG, "r") as f:
            feed_lines = [l for l in f.readlines() if l.strip()]
        lines.append(f"Feed log entries:     {len(feed_lines)}")
        if feed_lines:
            last = feed_lines[-1].strip()
            lines.append(f"  Last entry: {last}")
    else:
        lines.append("Feed log: empty")

    # Last activity
    lines.append("")
    all_times = []
    for f in broken_files + patch_files:
        match = re.search(r'\d{4}-\d{2}-\d{2}', f)
        if match:
            all_times.append(match.group())
    if all_times:
        lines.append(f"Last activity: {sorted(all_times)[-1]}")

    return "\n".join(lines)


# ── Tool: worm_list_broken ────────────────────────────────────

def worm_list_broken(input_str):
    """
    List all broken code files in the archive.
    """
    files = _list_dir(BROKEN_DIR)

    if not files:
        return "No broken code files in archive. CodeWorm hasn't detected any issues yet."

    lines = [f"Broken code archive — {len(files)} file(s):"]
    for f in sorted(files):
        path = os.path.join(BROKEN_DIR, f)
        size = os.path.getsize(path)
        lines.append(f"  {f}  ({size} bytes)")

    return "\n".join(lines)


# ── Tool: worm_read_broken ────────────────────────────────────

def worm_read_broken(input_str):
    """
    Read a specific broken code file from the archive.
    Input: filename (with or without path)
    """
    filename = os.path.basename(input_str.strip())
    if not filename:
        files = _list_dir(BROKEN_DIR)
        if not files:
            return "No broken files in archive."
        filename = sorted(files)[-1]

    filepath = os.path.join(BROKEN_DIR, filename)
    if not os.path.exists(filepath):
        # Try partial match
        files = _list_dir(BROKEN_DIR)
        matches = [f for f in files if filename.lower() in f.lower()]
        if matches:
            filepath = os.path.join(BROKEN_DIR, sorted(matches)[-1])
            filename = sorted(matches)[-1]
        else:
            return f"File not found in broken archive: {filename}"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Broken code: {filename}\n{'─' * 40}\n{content}"
    except Exception as e:
        return f"Could not read file: {e}"


# ── Helpers ───────────────────────────────────────────────────

def _read_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _list_dir(dirpath):
    try:
        if os.path.exists(dirpath):
            return [
                f for f in os.listdir(dirpath)
                if os.path.isfile(os.path.join(dirpath, f))
            ]
    except Exception:
        pass
    return []

# ── Tool: worm_hunt ───────────────────────────────────────────

def json_fix(input_str):
    """
    Reformat a JSON file to consistent 2-space indentation.
    Input: path to JSON file
    Syntax: [TOOL:json_fix: ~/Ethica/modules/mymodule/manifest.json]
    """
    from pathlib import Path
    import json as _json

    raw = input_str.strip()
    if not raw:
        return "json_fix — no path provided. Syntax: [TOOL:json_fix: /path/to/file.json]"

    p = Path(raw).expanduser().resolve()
    if not p.exists():
        return f"json_fix — file not found: {p}"
    if p.suffix.lower() != ".json":
        return f"json_fix — not a JSON file: {p.name}"

    try:
        original = p.read_text(encoding="utf-8")
        parsed = _json.loads(original)
    except _json.JSONDecodeError as e:
        return f"json_fix — parse error in {p.name}: {e}"
    except Exception as e:
        return f"json_fix — read error: {e}"

    reformatted = _json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"

    if reformatted == original:
        return f"json_fix — {p.name} is already consistently formatted. No changes made."

    try:
        p.write_text(reformatted, encoding="utf-8")
    except Exception as e:
        return f"json_fix — write error: {e}"

    added   = reformatted.count("\n")
    removed = original.count("\n")
    return (
        f"json_fix — {p.name} reformatted.\n"
        f"  Before : {len(original)} chars, {removed} lines\n"
        f"  After  : {len(reformatted)} chars, {added} lines\n"
        f"  Path   : {p}"
    )


def worm_fix_json(input_str):
    """
    Bulk-fix all JSON files flagged by WormHunter as inconsistently formatted.
    Reads worm_feed.log, deduplicates, runs json_fix on each flagged .json file.
    Syntax: [TOOL:worm_fix_json: run]
    """
    from pathlib import Path
    import re as _re

    feed_path = Path.home() / "Ethica/modules/codeworm/worm_feed.log"
    if not feed_path.exists():
        return "worm_fix_json — worm_feed.log not found. Run worm hunt first."

    try:
        lines = feed_path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return f"worm_fix_json — could not read feed: {e}"

    # Parse: collect .json files flagged with JSON formatting issue
    flagged = set()
    broken_pattern = _re.compile(r'\[WORM\]\[BROKEN\] (/[\w/._\- ]+\.json) —')
    for i, line in enumerate(lines):
        m = broken_pattern.search(line)
        if m:
            candidate = m.group(1).strip()
            # Check next line for JSON formatting flag
            if i + 1 < len(lines) and "JSON is not consistently formatted" in lines[i + 1]:
                flagged.add(candidate)

    if not flagged:
        return "worm_fix_json — no JSON formatting issues found in worm_feed.log. Run worm hunt first."

    fixed = []
    already_clean = []
    errors = []

    for path_str in sorted(flagged):
        result = json_fix(path_str)
        if "reformatted" in result:
            fixed.append(path_str)
        elif "already consistently formatted" in result:
            already_clean.append(path_str)
        else:
            errors.append(f"{path_str}: {result}")

    lines_out = [
        f"worm_fix_json — bulk JSON reformat complete.",
        f"{'─' * 50}",
        f"Flagged  : {len(flagged)}",
        f"Fixed    : {len(fixed)}",
        f"Clean    : {len(already_clean)}",
        f"Errors   : {len(errors)}",
    ]
    if fixed:
        lines_out.append(f"\n{'─' * 50}")
        lines_out.append("Reformatted:")
        for p in fixed:
            lines_out.append(f"  ✓ {p}")
    if errors:
        lines_out.append(f"\n{'─' * 50}")
        lines_out.append("Errors:")
        for e in errors:
            lines_out.append(f"  ✗ {e}")
    return "\n".join(lines_out)


def worm_hunt(input_str):
    """
    Run the WormHunter autonomous bug scanner on a path.
    Input: path to file or directory (defaults to ~/Ethica if empty)
    Syntax: [TOOL:worm_hunt: ~/myproject]
    """
    import sys
    from pathlib import Path

    worm_hunter_path = Path.home() / "Ethica/modules/worm_bot/worm_hunter.py"
    if not worm_hunter_path.exists():
        return "WormHunter not found — expected at ~/Ethica/modules/worm_bot/worm_hunter.py"

    # Dynamic import
    import importlib.util
    spec = importlib.util.spec_from_file_location("worm_hunter", worm_hunter_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    raw = input_str.strip()
    # If bare word with no path separators, ignore and use default
    target = raw if ("/" in raw or raw == "") else str(Path.home() / "Ethica")
    target = str(Path(target).expanduser().resolve())

    try:
        return mod.hunt_summary(target)
    except Exception as e:
        return f"WormHunter error: {e}"
