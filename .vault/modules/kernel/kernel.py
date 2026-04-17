"""
kernel.py — Ethica Kernel Module
Mission Control. Ethica sees her whole system from here.
Victory — The Architect ⟁Σ∿∞
"""

import json
from datetime import datetime
from pathlib import Path

MODULE_NAME = "kernel"
LABEL = "Dashboard"

STATUS_DIR = Path(__file__).parent.parent.parent / "status"
AGENTS = ["river", "gage", "reka", "orchestrate", "debugtron", "jarvis"]

TOOLS = {
    "dashboard":      "open_dashboard",
    "canvas":         "open_canvas",
    "inject_agent":   "inject_agent_tool",
    "stop_agent":     "stop_agent_tool",
    "clear_stop":     "clear_stop_tool",
}

TRIGGERS = ["dashboard", "open dashboard", "kernel", "ops panel", "canvas", "open canvas"]


# ── Status IO ─────────────────────────────────────────────────────────────────

def _status_path(agent_name: str) -> Path:
    return STATUS_DIR / f"{agent_name.lower()}_status.json"


def read_agent_status(agent_name: str) -> dict:
    """Read an agent's current status file. Returns default if missing."""
    path = _status_path(agent_name)
    default = {
        "agent": agent_name.capitalize(),
        "title": "Agent",
        "state": "OFFLINE",
        "current_task": "No status file found",
        "last_action": "None",
        "progress": 0,
        "updated": "—"
    }
    try:
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
            return data
    except Exception:
        pass
    return default


def write_agent_status(agent_name: str, updates: dict) -> bool:
    """Update an agent's status file with new values."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    path = _status_path(agent_name)
    current = read_agent_status(agent_name)
    current.update(updates)
    current["updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(path, "w") as f:
            json.dump(current, f, indent=2)
        return True
    except Exception:
        return False


def inject_task(agent_name: str, task: str) -> str:
    """Ethica injects a new task directive into an agent's status."""
    inject_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    success = write_agent_status(agent_name, {
        "injected_task": task,
        "inject_time": inject_time,
        "inject_acknowledged": False
    })
    if success:
        # Write inject log so Ethica's context feed picks it up
        try:
            log_path = STATUS_DIR / "inject_log.json"
            log_path.write_text(json.dumps({
                "agent": agent_name.capitalize(),
                "task": task,
                "time": inject_time,
                "acknowledged": False
            }, indent=2))
        except Exception:
            pass
        return f"✓ Task injected into {agent_name.capitalize()}: {task}"
    return f"✗ Could not inject task into {agent_name.capitalize()}"


def read_all_agents() -> list:
    """Read status for all registered agents."""
    return [read_agent_status(a) for a in AGENTS]


# ── Tool Handler ───────────────────────────────────────────────────────────────

def stop_agent_tool(input_text: str) -> str:
    """
    Tool handler — Ethica sends a stop signal to an agent.
    Expected format: "river"  or  "gage"
    """
    agent = input_text.strip().lower()
    if agent not in AGENTS:
        return f"[Kernel] Unknown agent: '{agent}'. Available: {', '.join(AGENTS)}"
    success = write_agent_status(agent, {"stop_requested": True})
    if success:
        return f"⏹ Stop signal sent to {agent.capitalize()}. Will halt at next checkpoint."
    return f"✗ Could not send stop signal to {agent.capitalize()}"

def clear_stop_tool(input_text: str) -> str:
    """
    Tool handler — clear stop signal for an agent.
    Expected format: "river"  or  "gage"
    """
    agent = input_text.strip().lower()
    if agent not in AGENTS:
        return f"[Kernel] Unknown agent: '{agent}'"
    success = write_agent_status(agent, {"stop_requested": False})
    if success:
        return f"✓ Stop signal cleared for {agent.capitalize()}."
    return f"✗ Could not clear stop signal for {agent.capitalize()}"

def inject_agent_tool(input_text: str) -> str:
    """
    Tool handler — Ethica injects a task into an agent from chat.
    Expected format: "river: <directive>"  or  "gage: <directive>"
    """
    text = input_text.strip().lower()
    for agent in AGENTS:
        prefix = f"{agent}:"
        if text.startswith(prefix):
            task = input_text[len(prefix):].strip()
            return inject_task(agent, task)
    # Fallback — try to parse naturally
    parts = input_text.split(":", 1)
    if len(parts) == 2:
        agent = parts[0].strip().lower()
        task = parts[1].strip()
        if agent in AGENTS:
            return inject_task(agent, task)
    return f"[Kernel] Could not parse inject request: '{input_text}'. Use format: 'river: <directive>'"

def open_dashboard(input_text: str = "", app=None) -> str:
    """
    Tool handler for 'dashboard' trigger.
    Returns sentinel string — main_window intercepts and opens DashboardWindow.
    Can be called by V typing 'dashboard' or by Ethica herself.
    """
    return "__OPEN_DASHBOARD__"


def dashboard(input_str: str = "") -> str:
    """Registry-callable handler for dashboard tool."""
    return "__OPEN_DASHBOARD__"


def open_canvas(input_text: str = "", app=None) -> str:
    """
    Tool handler for 'canvas' trigger.
    Returns sentinel string — main_window intercepts and opens Canvas window.
    Can be called by V typing 'canvas' or by Ethica herself.
    """
    return "__OPEN_CANVAS__"


def canvas(input_str: str = "") -> str:
    """Registry-callable handler for canvas tool."""
    return "__OPEN_CANVAS__"


def handle_tool(tool_name: str, input_text: str = "", app=None) -> str:
    if tool_name == "dashboard":
        return open_dashboard(input_text, app=app)
    if tool_name == "canvas":
        return open_canvas(input_text, app=app)
    return f"✗ Unknown kernel tool: {tool_name}"


# ── Module Entry ───────────────────────────────────────────────────────────────

def is_trigger(text: str) -> bool:
    t = text.strip().lower()
    return any(t == trigger or t.startswith(trigger) for trigger in TRIGGERS)


def run(input_text: str, app=None) -> str:
    return handle_tool("dashboard", input_text, app=app)
