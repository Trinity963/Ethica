# debugtron.py — Ethica bridge for Debugtron
# Debugtron: The King of Debugging — any language, any error
# Trinity's core preserved. This file wraps and wires only.

import subprocess
import sys
from pathlib import Path


def _debugtron_status(state, task, action, progress=0):
    try:
        from modules.kernel.kernel import write_agent_status
        write_agent_status("debugtron", {
            "state": state,
            "task": task,
            "last_action": action,
            "progress": progress,
        })
    except Exception:
        pass


def _check_stop() -> bool:
    try:
        from modules.kernel.kernel import read_agent_status
        s = read_agent_status("debugtron")
        return s.get("stop_requested", False)
    except Exception:
        return False


# ── Tool handlers ─────────────────────────────────────────────

def debugtron_analyze(args: str) -> str:
    """Analyze an error message or traceback and suggest a fix."""
    from modules.debugtron.debugtron_ai import create_debugtron
    dt = create_debugtron()
    _debugtron_status("ACTIVE", args[:60], "analyze", 10)
    result = dt.ai_analyze_error(args.strip())
    _debugtron_status("IDLE", "Awaiting directive", "analyze complete", 100)
    return result


def debugtron_run(args: str) -> str:
    """Run a file or snippet and capture errors for Debugtron to analyze."""
    path = Path(args.strip()).expanduser()
    if not path.exists():
        return f"✗ File not found: {path}"
    _debugtron_status("ACTIVE", str(path), "run + debug", 10)
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            _debugtron_status("IDLE", "Awaiting directive", "run clean", 100)
            return f"✓ Clean run\n{result.stdout}"
        else:
            from modules.debugtron.debugtron_ai import create_debugtron
            dt = create_debugtron()
            analysis = dt.ai_analyze_error(result.stderr)
            _debugtron_status("IDLE", "Awaiting directive", "run + analyzed", 100)
            return f"✗ Error detected:\n{result.stderr}\n\nDebug analysis:\n{analysis}"
    except subprocess.TimeoutExpired:
        _debugtron_status("IDLE", "Timeout", "run timeout", 0)
        return "✗ Execution timed out after 30s"
    except Exception as e:
        _debugtron_status("IDLE", "Error", "run exception", 0)
        return f"✗ {e}"


def debugtron_verify(args: str) -> str:
    """Verify Python file syntax via ast.parse."""
    import ast
    path = Path(args.strip()).expanduser()
    if not path.exists():
        return f"✗ File not found: {path}"
    _debugtron_status("ACTIVE", str(path), "verify", 50)
    try:
        content = path.read_text()
        ast.parse(content)
        _debugtron_status("IDLE", "Awaiting directive", "verify clean", 100)
        return f"✓ Syntax clean: {path.name}"
    except SyntaxError as e:
        _debugtron_status("IDLE", "Syntax error found", "verify failed", 0)
        return f"✗ Syntax error line {e.lineno}: {e.msg}"


def debugtron_status(args: str) -> str:
    """Return Debugtron's current status."""
    try:
        from modules.kernel.kernel import read_agent_status
        s = read_agent_status("debugtron")
        return (
            f"Debugtron — {s.get('state','IDLE')}\n"
            f"Task: {s.get('task','—')}\n"
            f"Last action: {s.get('last_action','—')}\n"
            f"Progress: {s.get('progress',0)}%"
        )
    except Exception as e:
        return f"✗ Status read error: {e}"


# ── Tool registry ─────────────────────────────────────────────

TOOLS = {
    "debugtron_analyze": debugtron_analyze,
    "debugtron_run":     debugtron_run,
    "debugtron_verify":  debugtron_verify,
    "debugtron_status":  debugtron_status,
}
