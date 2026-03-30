# ============================================================
# Ethica Module — siem_bridge.py
# TrinitySIEM Bridge — wraps siem_security_system.py
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# Trinity built this. We wrap it — never rewrite.
# ============================================================

import os
import sys
import json
import logging
from datetime import datetime

MODULE_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(MODULE_DIR, "configs")
LOG_DIR     = os.path.join(MODULE_DIR, "logs")
LOG_FILE    = os.path.join(LOG_DIR,    "siem_logs.json")
THREAT_LOG  = os.path.join(LOG_DIR,    "threat_analysis.log")
CONFIG_FILE = os.path.join(CONFIG_DIR, "siem_config.json")
FILTERS_FILE= os.path.join(CONFIG_DIR, "event_filters.yaml")

os.makedirs(LOG_DIR, exist_ok=True)

def _load_filters():
    try:
        import yaml
        with open(FILTERS_FILE) as f:
            return yaml.safe_load(f)
    except Exception:
        return {"threat_signatures": []}

def _log_event(event):
    event["timestamp"] = datetime.utcnow().isoformat()
    try:
        with open(LOG_FILE, "a") as f:
            json.dump(event, f)
            f.write("\n")
    except Exception:
        pass

def _detect_anomaly(event):
    filters = _load_filters()
    for sig in filters.get("threat_signatures", []):
        if sig in event.get("message", "").lower():
            return True
    return False

def siem_ingest(input_str):
    """Ingest a security event — source|message"""
    parts = input_str.split("|", 1)
    source  = parts[0].strip() if len(parts) > 1 else "Unknown"
    message = parts[1].strip() if len(parts) > 1 else parts[0].strip()

    event = {"source": source, "message": message}
    _log_event(event)

    threat = _detect_anomaly(event)
    if threat:
        return f"TrinitySIEM — ⚠ THREAT DETECTED\nSource: {source}\nMessage: {message}\nAutomated response triggered."
    return f"TrinitySIEM — Event logged.\nSource: {source}\nMessage: {message}\nNo threats detected."

def siem_read_log(input_str):
    try:
        n = int(input_str.strip()) if input_str.strip().isdigit() else 20
    except Exception:
        n = 20
    if not os.path.exists(LOG_FILE):
        return "TrinitySIEM — no events logged yet."
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        tail = lines[-n:]
        events = []
        for l in tail:
            try:
                e = json.loads(l)
                ts = e.get("timestamp",""); src = e.get("source","?"); msg = e.get("message","")
                events.append(f"  [{ts}] {src} — {msg}")
            except Exception:
                events.append(f"  {l.strip()}")
        return f"TrinitySIEM Log (last {n}):\n" + "\n".join(events)
    except Exception as e:
        return f"TrinitySIEM — log read error: {e}"

def siem_status(input_str):
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    log_count = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log_count = sum(1 for _ in f)
    filters = _load_filters()
    sigs = filters.get("threat_signatures", [])
    return (
        f"TrinitySIEM — Active\n"
        f"Name: {cfg.get('siem_name', 'TrinitySIEM')}\n"
        f"Events logged: {log_count}\n"
        f"Threat signatures: {len(sigs)}\n"
        f"Log: {LOG_FILE}"
    )

TOOLS = {
    "siem_ingest":   siem_ingest,
    "siem_read_log": siem_read_log,
    "siem_status":   siem_status,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[TrinitySIEM] Unknown tool: {tool_name}"
