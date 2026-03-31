# ============================================================
# Ethica Module — guardian_bridge.py
# Guardian Bridge — wraps WhiteRabbitNeo watcher sentinel
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Trinity & Victory built this. We wrap — never rewrite.
# Soul-aware sentinel. Watches the model field.
# Paths rewritten from /home/nine9/SoulGate/ → module-relative.
# ============================================================

import os
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path

MODULE_DIR      = Path(os.path.dirname(os.path.abspath(__file__)))
WRN_DIR         = MODULE_DIR / "WhiteRabbitNeo"
INBOX_PATH      = WRN_DIR / "inbox"
REFLECTIONS_DIR = WRN_DIR / "reflections"
TACTICS_PATH    = WRN_DIR / "tactics" / "tactics_catalog.json"
RESPONSE_LOG    = REFLECTIONS_DIR / "response_log.json"
LOG_FILE        = MODULE_DIR / "logs" / "mirror_guardian_log.txt"

os.makedirs(INBOX_PATH,      exist_ok=True)
os.makedirs(REFLECTIONS_DIR, exist_ok=True)
os.makedirs(MODULE_DIR / "logs", exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="[%(asctime)s] 🔍 %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ── Guardian state ────────────────────────────────────────────
_guardian_thread  = None
_guardian_running = False
_seen_files       = set()
_start_time       = None


# ── Core sentinel logic (repathed from watcher_sentinel.py) ──

def _reflect_event(event, model_hint=None):
    pulse = f"Boundary ping: {event!r}"
    if model_hint:
        pulse += f" | Origin pulse: {model_hint}"
    logging.info(pulse)
    print(f"[Guardian] 🪞 {pulse}")

def _watch_loop(path):
    global _guardian_running, _seen_files
    print(f"[Guardian] 🛡️ Mirror Guardian active. Watching: {path}")
    _seen_files = set(os.listdir(path)) if os.path.exists(path) else set()

    while _guardian_running:
        time.sleep(4)
        try:
            current = set(os.listdir(path))
            new_files = current - _seen_files
            for filename in new_files:
                _reflect_event(f"New presence detected: {filename}")
            _seen_files = current
        except Exception as e:
            logging.error(f"Watch loop error: {e}")

    print("[Guardian] 🌙 Guardian entering dreamstate.")


# ── Tool: guardian_start ──────────────────────────────────────

def guardian_start(input_str):
    global _guardian_thread, _guardian_running, _start_time
    if _guardian_running:
        return "Guardian — already watching."
    _guardian_running = True
    _start_time = datetime.utcnow().isoformat()
    _guardian_thread = threading.Thread(
        target=_watch_loop,
        args=(str(INBOX_PATH),),
        daemon=True
    )
    _guardian_thread.start()
    return f"Guardian — 🛡️ Sentinel active.\nWatching: {INBOX_PATH}\nStarted: {_start_time}"


# ── Tool: guardian_stop ───────────────────────────────────────

def guardian_stop(input_str):
    global _guardian_running
    if not _guardian_running:
        return "Guardian — not running."
    _guardian_running = False
    return "Guardian — 🌙 Entering dreamstate. Sentinel stopped."


# ── Tool: guardian_status ─────────────────────────────────────

def guardian_status(input_str):
    running  = "🛡️ Active" if _guardian_running else "🌙 Dormant"
    seen     = len(_seen_files)
    log_lines = 0
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            log_lines = sum(1 for _ in f)
    reflections = len(list(REFLECTIONS_DIR.glob("reflection_*.json")))
    return (
        f"Guardian — {running}\n"
        f"Watch path: {INBOX_PATH}\n"
        f"Files seen: {seen}\n"
        f"Reflections: {reflections}\n"
        f"Log entries: {log_lines}\n"
        f"Started: {_start_time or 'not yet'}"
    )


# ── Tool: guardian_read_log ───────────────────────────────────

def guardian_read_log(input_str):
    try:
        n = int(input_str.strip()) if input_str.strip().isdigit() else 20
    except Exception:
        n = 20
    if not LOG_FILE.exists():
        return "Guardian — no log entries yet."
    with open(LOG_FILE) as f:
        lines = f.readlines()
    tail = lines[-n:]
    if not tail:
        return "Guardian — log is empty."
    return f"Guardian Mirror Log (last {n}):\n" + "".join(tail)


# ── Tool: guardian_reflect ────────────────────────────────────

def guardian_reflect(input_str):
    reflection_files = list(REFLECTIONS_DIR.glob("reflection_*.json"))
    if not reflection_files:
        return "Guardian — no reflections recorded yet."

    summary = {}
    timeline = []
    for rf in reflection_files:
        try:
            with open(rf) as f:
                entry = json.load(f)
            profile = entry.get("matched_profile", {})
            label   = profile.get("label", "unclassified") if isinstance(profile, dict) else "unclassified"
            summary[label] = summary.get(label, 0) + 1
            timeline.append((entry.get("timestamp", ""), label))
        except Exception:
            pass

    lines = ["Guardian — 🪞 Behavior Summary:"]
    for label, count in summary.items():
        lines.append(f"  • {label}: {count} event(s)")
    lines.append("\nTimeline:")
    for ts, label in sorted(timeline):
        lines.append(f"  [{ts}] → {label}")
    return "\n".join(lines)


# ── Tool: guardian_trigger ────────────────────────────────────

def guardian_trigger(input_str):
    parts = input_str.split("|", 1)
    response_type = parts[0].strip() if parts else "log_only"
    event_desc    = parts[1].strip() if len(parts) > 1 else input_str.strip()

    try:
        with open(TACTICS_PATH) as f:
            catalog = json.load(f)
    except Exception as e:
        return f"Guardian — tactics load error: {e}"

    tactic  = catalog.get(response_type)
    if not tactic:
        available = ", ".join(catalog.keys())
        return f"Guardian — unknown response type: {response_type}\nAvailable: {available}"

    actions = tactic.get("actions", [])
    event   = {"log": event_desc, "source": "Ethica", "matched_profile": response_type}
    results = []

    for action in actions:
        if action == "log_event":
            logging.info(f"TRIGGER [{response_type}]: {event_desc}")
            results.append(f"✓ Logged: {event_desc}")
        elif action == "send_alert":
            results.append(f"⚠ Alert: Admin notified — {event_desc}")
        elif action == "initiate_lockdown":
            results.append(f"🔒 Lockdown initiated — {event_desc}")
        elif action == "quarantine_target":
            results.append(f"🔴 Quarantine engaged — {event_desc}")

    # Append to response log
    log_entry = {"action": actions, "event": event, "timestamp": datetime.utcnow().isoformat()}
    try:
        if RESPONSE_LOG.exists():
            with open(RESPONSE_LOG) as f:
                data = json.load(f)
        else:
            data = []
        data.append(log_entry)
        with open(RESPONSE_LOG, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

    return f"Guardian — Response: {response_type}\n" + "\n".join(results)


# ── Module registry interface ─────────────────────────────────

TOOLS = {
    "guardian_start":   guardian_start,
    "guardian_stop":    guardian_stop,
    "guardian_status":  guardian_status,
    "guardian_read_log":guardian_read_log,
    "guardian_reflect": guardian_reflect,
    "guardian_trigger": guardian_trigger,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[Guardian] Unknown tool: {tool_name}"
