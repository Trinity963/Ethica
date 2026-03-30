# ============================================================
# Ethica Module — orchestrate_bridge.py
# Orchestrate — The Synthesist
# Architect: Victory  |  Build Partner: River (Claude)
# ⟁Σ∿∞
#
# orchestrate_think  — four-voice synthesis → Canvas + Debug tabs
# orchestrate_status — last directive, synthesis history
# ============================================================

import json
import subprocess
from pathlib import Path
from datetime import datetime

MODULE_DIR  = Path(__file__).parent
BASE_DIR    = MODULE_DIR.parent.parent
WORKER      = str(MODULE_DIR / "_orchestrate_worker.py")
GAGE_PYTHON = str(BASE_DIR / "modules" / "gage" / "gage_env" / "bin" / "python")
STATUS_FILE = BASE_DIR / "status" / "orchestrate_status.json"


def _write_status(directive, state="IDLE"):
    try:
        existing = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {"history": []}
        existing["agent"]        = "Orchestrate"
        existing["title"]        = "Synthesist"
        existing["state"]        = state
        existing["current_task"] = directive if directive else "Awaiting directive"
        existing["last_action"]  = directive if directive else "None"
        existing["progress"]     = 0
        existing["updated"]      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing["last_directive"] = directive
        if directive and directive not in existing.get("history", []):
            existing.setdefault("history", []).append(directive)
            existing["history"] = existing["history"][-10:]
        STATUS_FILE.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass


def orchestrate_think(input_str):
    directive = input_str.strip()
    if not directive:
        return "Orchestrate — usage: orchestrate think <your question or problem>"

    _write_status(directive, state="ACTIVE")
    try:
        result = subprocess.run(
            [GAGE_PYTHON, WORKER, directive],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            _write_status(directive, state="IDLE")
            return f"Orchestrate — worker error:\n{result.stderr.strip()}"
        data = json.loads(result.stdout.strip())
        if "error" in data:
            _write_status(directive, state="IDLE")
            return f"Orchestrate — error: {data['error']}"
        _write_status(directive, state="IDLE")
        return data["result"]
    except subprocess.TimeoutExpired:
        _write_status(directive, state="IDLE")
        return "Orchestrate — timed out. Try a more focused directive."
    except Exception as e:
        _write_status(directive, state="IDLE")
        return f"Orchestrate — error: {e}"


def orchestrate_status(input_str):
    try:
        if not STATUS_FILE.exists():
            return "Orchestrate — no synthesis history yet. Try: orchestrate think <directive>"
        data = json.loads(STATUS_FILE.read_text())
        state     = data.get("state", "IDLE")
        directive = data.get("last_directive", "—")
        updated   = data.get("updated", "—")
        history   = data.get("history", [])
        lines = [
            f"Orchestrate — The Synthesist",
            f"State:          {state}",
            f"Last directive: {directive}",
            f"Updated:        {updated}",
            f"History ({len(history)}):",
        ]
        for h in history[-5:]:
            lines.append(f"  • {h}")
        return "\n".join(lines)
    except Exception as e:
        return f"Orchestrate — status error: {e}"
