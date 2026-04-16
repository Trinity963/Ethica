# ============================================================
# Ethica Module — gage_bridge.py
# Gage AI Bridge
# Architect: Victory  |  Build Partner: River aka Claude
# ⟁Σ∿∞
#
# Gage is an agent — humor, confidence, tactical mindset.
# gage_launch  — fires full Streamlit app in browser
# gage_chat    — Gage persona via Ethica's loaded model
# gage_read_code — Gage reviews a file
# ============================================================

import os
import sys
import subprocess
import logging
import threading
from pathlib import Path

MODULE_DIR  = Path(os.path.dirname(os.path.abspath(__file__)))
GAGE_APP    = MODULE_DIR / "gage_ai.py"

_launch_proc   = None
_launch_count  = 0

GAGE_SYSTEM = (
    "You are Gage — an advanced AI agent with humor, confidence, "
    "and a tactical mindset. You are direct, sharp, and never boring. "
    "You give real answers, not filler. When reviewing code you are "
    "precise, critical, and constructive. You speak like someone who "
    "has seen everything and fixed most of it."
)


def _gage_status(state, task, action, progress=0):
    """Write Gage's live status to the dashboard status file."""
    try:
        from modules.kernel.kernel import write_agent_status
        write_agent_status("gage", {
            "state": state,
            "current_task": task,
            "last_action": action,
            "progress": progress
        })
    except Exception:
        pass


def _check_stop() -> bool:
    """Check if a stop signal has been sent to Gage."""
    try:
        from modules.kernel.kernel import read_agent_status
        data = read_agent_status("gage")
        return data.get("stop_requested", False)
    except Exception:
        return False


def _check_inject() -> str:
    """Check if Ethica has injected a task for Gage. Acknowledge on read."""
    try:
        from modules.kernel.kernel import read_agent_status, write_agent_status
        data = read_agent_status("gage")
        if data.get("injected_task") and not data.get("inject_acknowledged", True):
            task = data["injected_task"]
            write_agent_status("gage", {"inject_acknowledged": True})
            return task
    except Exception:
        pass
    return ""


# ── Tool: gage_launch ─────────────────────────────────────────

def gage_launch(input_str):
    global _launch_proc, _launch_count

    GAGE_ENV_PYTHON = MODULE_DIR / "gage_env" / "bin" / "python"
    GAGE_ENV_STREAMLIT = MODULE_DIR / "gage_env" / "bin" / "streamlit"

    # Check if gage_env streamlit is available
    if not GAGE_ENV_STREAMLIT.exists():
        return (
            "Gage — gage_env not found.\n"
            f"Expected: {GAGE_ENV_STREAMLIT}\n"
            "Build with: python3 -m venv gage_env && gage_env/bin/pip install streamlit"
        )

    if not GAGE_APP.exists():
        return f"Gage — app file not found: {GAGE_APP}"

    if _launch_proc and _launch_proc.poll() is None:
        return "Gage — already running in browser. Check http://localhost:8501"

    def _run():
        global _launch_proc, _launch_count
        _launch_proc = subprocess.Popen(
            [str(GAGE_ENV_PYTHON), "-m", "streamlit", "run", str(GAGE_APP)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        _launch_count += 1

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    import time
    time.sleep(1.5)

    return (
        "Gage — 🤖 Launching full UI...\n"
        "Browser: http://localhost:8501\n"
        "Voice, 3D avatar, TTS all active in Streamlit.\n"
        "Use gage_status to check."
    )


# ── Tool: gage_chat ───────────────────────────────────────────

def gage_chat(input_str):
    if _check_stop():
        return "Gage — stop signal active. Clear with: clear stop"

    message = input_str.strip()
    if not message:
        return "Gage — nothing to respond to."

    injected = _check_inject()
    if injected:
        message = f"[Injected task from Ethica]: {injected}\n\n{message}" if message else f"[Injected task from Ethica]: {injected}"

    _gage_status("ACTIVE", message[:60], "gage_chat", 10)

    # Use Ollama — same as Trinity/River/J.A.R.V.I.S.
    try:
        sys.path.insert(0, str(MODULE_DIR.parent.parent))
        from core.ollama_connector import OllamaConnector

        connector = OllamaConnector(model="minimax-m2.7:cloud")

        messages = [
            {"role": "system", "content": GAGE_SYSTEM},
            {"role": "user",   "content": message}
        ]
        response = connector.chat(messages, stream=False)
        import re
        clean = re.sub(r'<think>[\s\S]*?</think>', '', response, flags=re.IGNORECASE).strip()
        _gage_status("IDLE", "Awaiting directive", "gage_chat complete", 100)
        return f"Gage: {clean}"

    except Exception as e:
        return (
            f"Gage — model not available: {e}\n"
            f"Launch full UI with: gage launch"
        )
        _gage_status("IDLE", "Awaiting directive", "gage_chat error", 0)


# ── Tool: gage_read_code ──────────────────────────────────────

def gage_read_code(input_str):
    filepath = os.path.expanduser(input_str.strip())
    logging.info(f"[GAGE_READ] received: {repr(filepath)}, exists: {os.path.exists(filepath)}")
    if not filepath or not os.path.exists(filepath):
        return f"Gage — file not found: {filepath}"

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        return f"Gage — file read error: {e}"

    # Truncate if massive
    if len(code) > 500:
        code = code[:500] + "\n... [truncated]"

    try:
        import requests, re
        ext = os.path.splitext(filepath)[1].lstrip('.') or 'python'
        messages = [
            {"role": "system", "content": GAGE_SYSTEM},
            {"role": "user",   "content": (
                f"You are reviewing the EXACT code below. "
                f"Do NOT invent or recall code from memory. "
                f"Only reference what is literally written here.\n\n"
                f"File: {filepath}\n\n"
                f"```{ext}\n{code}\n```\n\n"
                f"Give a 3-line code review."
            )}
        ]
        sys.path.insert(0, str(MODULE_DIR.parent.parent))
        from core.ollama_connector import OllamaConnector
        connector = OllamaConnector(model="minimax-m2.7:cloud")
        response = connector.chat(messages, stream=False)
        clean = re.sub(r'<think>[\s\S]*?</think>', '', response, flags=re.IGNORECASE).strip()
        return f"Gage — Code Review: {filepath}\n\n{clean}\n\n[DEBUG:Gage:{ext}:\n{code}]"
    except Exception as e:
        return f"Gage — model error: {e}"


# ── Tool: gage_status ─────────────────────────────────────────

def gage_status(input_str):
    running = (
        "🟢 Running" if _launch_proc and _launch_proc.poll() is None
        else "⚫ Not launched"
    )
    return (
        f"Gage — Status\n"
        f"Streamlit UI: {running}\n"
        f"Launch count: {_launch_count}\n"
        f"App: {GAGE_APP}\n"
        f"URL: http://localhost:8501"
    )



# ── Tool: gage_stop ──────────────────────────────────────────
def gage_stop(input_str):
    """Kill the Streamlit process group cleanly."""
    global _launch_proc
    if not _launch_proc or _launch_proc.poll() is not None:
        return "Gage — not running."
    try:
        import signal
        os.killpg(_launch_proc.pid, signal.SIGTERM)
        _launch_proc = None
        return "Gage — stopped cleanly."
    except Exception as e:
        return f"Gage — stop error: {e}"


# ── Tool: gage_vision ─────────────────────────────────────────
def gage_vision(input_str):
    """Describe an image using BLIP vision model via gage_env."""
    filepath = os.path.expanduser(input_str.strip())
    if not filepath or not os.path.exists(filepath):
        return f"Gage Vision — file not found: {filepath}"

    GAGE_ENV_PYTHON = str(MODULE_DIR / "gage_env" / "bin" / "python")
    # Use system python3 for vision worker — only needs requests + base64
    import shutil
    VISION_PYTHON = shutil.which("python3") or GAGE_ENV_PYTHON
    vision_script = str(MODULE_DIR / "_vision_worker.py")

    worker = Path(vision_script)
    if not worker.exists():
        worker.write_text(
            "import sys\n"
            "from PIL import Image\n"
            "from transformers import BlipProcessor, BlipForConditionalGeneration\n"
            "import torch\n\n"
            "filepath = sys.argv[1]\n"
            "processor = BlipProcessor.from_pretrained(\"Salesforce/blip-image-captioning-base\")\n"
            "model = BlipForConditionalGeneration.from_pretrained(\"Salesforce/blip-image-captioning-base\")\n"
            "model.eval()\n\n"
            "image = Image.open(filepath).convert(\"RGB\")\n"
            "inputs = processor(image, return_tensors=\"pt\")\n"
            "with torch.no_grad():\n"
            "    out = model.generate(**inputs, max_new_tokens=100)\n"
            "print(processor.decode(out[0], skip_special_tokens=True))\n"
        )

    try:
        result = subprocess.run(
            [VISION_PYTHON, vision_script, filepath],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode != 0:
            return f"Gage Vision — error:\n{result.stderr.strip()}"
        description = result.stdout.strip()
        return f"Gage Vision — {filepath}\n\n{description}"
    except subprocess.TimeoutExpired:
        return "Gage Vision — timed out. Image inference requires GPU. Pending M5 upgrade."
    except Exception as e:
        return f"Gage Vision — error: {e}"

# ── Gage memory tools ───────────────────────────────────────
from modules.gage.gage_memory import gage_wake, gage_distill_run

# ── Module registry interface ─────────────────────────────────
TOOLS = {
    "gage_launch":    gage_launch,
    "gage_chat":      gage_chat,
    "gage_read_code": gage_read_code,
    "gage_status":    gage_status,
    "gage_stop":      gage_stop,
    "gage_vision":    gage_vision,
    "gage_wake":       gage_wake,
    "gage_distill_run": gage_distill_run,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[Gage] Unknown tool: {tool_name}"
