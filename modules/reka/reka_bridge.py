# ============================================================
# Ethica Module — reka_bridge.py
# Reka — Systems Inventor
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# reka_invent  — brainstorm + prototype → Canvas + Debug tabs
# reka_status  — last concept, prototype history
# ============================================================

import json
import subprocess
from pathlib import Path
from datetime import datetime

MODULE_DIR  = Path(__file__).parent
BASE_DIR    = MODULE_DIR.parent.parent
WORKER      = str(MODULE_DIR / "_reka_worker.py")
GAGE_PYTHON = str(BASE_DIR / "modules" / "gage" / "gage_env" / "bin" / "python")
STATUS_FILE = BASE_DIR / "status" / "reka_status.json"


def _write_status(concept, state="IDLE"):
    try:
        existing = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {"history": []}
        existing["agent"]        = "Reka"
        existing["title"]        = "Inventor"
        existing["state"]        = state
        existing["current_task"] = concept if concept else "Awaiting directive"
        existing["last_action"]  = concept if concept else "None"
        existing["progress"]     = 0
        existing["updated"]      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing["last_concept"] = concept
        if concept and concept not in existing.get("history", []):
            existing.setdefault("history", []).append(concept)
            existing["history"] = existing["history"][-10:]
        STATUS_FILE.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass


def reka_invent(input_str):
    idea = input_str.strip()
    if not idea:
        return "Reka — usage: reka invent <describe your idea>"

    _write_status(idea, state="ACTIVE")
    try:
        result = subprocess.run(
            [GAGE_PYTHON, WORKER, idea],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            _write_status(idea, state="IDLE")
            return f"Reka — worker error:\n{result.stderr.strip()}"
        data = json.loads(result.stdout.strip())
        if "error" in data:
            _write_status(idea, state="IDLE")
            return f"Reka — error: {data['error']}"
        _write_status(idea, state="IDLE")
        return data["result"]
    except subprocess.TimeoutExpired:
        _write_status(idea, state="IDLE")
        return "Reka — timed out. Try a more focused idea."
    except Exception as e:
        _write_status(idea, state="IDLE")
        return f"Reka — error: {e}"


def reka_status(input_str):
    try:
        if not STATUS_FILE.exists():
            return "Reka — no prototype history yet. Try: reka invent <idea>"
        data = json.loads(STATUS_FILE.read_text())
        state   = data.get("state", "IDLE")
        concept = data.get("last_concept", "—")
        updated = data.get("updated", "—")
        history = data.get("history", [])
        lines = [
            "Reka — Systems Inventor",
            f"State:        {state}",
            f"Last concept: {concept}",
            f"Updated:      {updated}",
            f"History ({len(history)}):",
        ]
        for h in history[-5:]:
            lines.append(f"  • {h}")
        return "\n".join(lines)
    except Exception as e:
        return f"Reka — status error: {e}"
