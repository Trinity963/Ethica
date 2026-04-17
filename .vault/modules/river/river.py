# ============================================================
# Ethica Module — river.py
# River — The Builder Agent
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# River is the surgical builder.
# Gage reviews. River builds.
#
# river_read   — grep + sed combined, read exact lines
# river_patch  — surgical string replace with ast.parse verify
# river_verify — ast.parse check on any Python file
# river_plan   — break a build task into sequential steps
# river_run    — execute a shell command and return output
#
# River never rewrites what can be patched.
# River never asks V to paste a full file.
# River always verifies after every write.
# ============================================================

import ast
import os
import re
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

MODULE_DIR = Path(__file__).parent
BASE_DIR   = MODULE_DIR.parent.parent

# Memory file paths
RIVER_CONV_PATH  = BASE_DIR / "memory" / "river_conversational.json"
RIVER_BUILD_PATH = BASE_DIR / "memory" / "river_build.json"
SESSION_CONTEXT_PATH = BASE_DIR / "status" / "session_context.json"
RIVER_STATE_PATH     = BASE_DIR / "memory" / "river_state.json"

# ── Memory helpers ────────────────────────────────────────────
def _load_river_memory():
    """Load both memory streams and return compressed context string."""
    sections = []
    for label, path in [("Conversation history", RIVER_CONV_PATH),
                        ("Build history",         RIVER_BUILD_PATH)]:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                entries = data.get("entries", [])[-20:]  # last 20 per stream
                if entries:
                    lines = [f"{label}:"]
                    for e in entries:
                        lines.append(f"  [{e.get('date','')}] {e.get('note','')}")
                    sections.append("\n".join(lines))
            except Exception:
                pass
    return "\n\n".join(sections) if sections else ""


def _load_session_context():
    """Load live session context written by V at session start."""
    if SESSION_CONTEXT_PATH.exists():
        try:
            data = json.loads(SESSION_CONTEXT_PATH.read_text())
            summary = data.get("summary", "").strip()
            if summary:
                return summary
        except Exception:
            pass
    return ""


def _load_river_state():
    """
    Load river_state.json and return a diff-aware context string.
    If file does not exist — creates blank baseline and returns empty string.
    """
    if not RIVER_STATE_PATH.exists():
        baseline = {
            "last_updated": datetime.now().isoformat(timespec="seconds"),
            "session": "",
            "agents": {},
            "canvas_tabs": [],
            "vault_count": 0,
            "last_drop": None,
            "notes": ""
        }
        RIVER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        RIVER_STATE_PATH.write_text(json.dumps(baseline, indent=2))
        return ""
    try:
        data = json.loads(RIVER_STATE_PATH.read_text())
        lines = [f"Last state ({data.get('last_updated','unknown')}):"]
        agents = data.get("agents", {})
        if agents:
            lines.append("  Agents: " + ", ".join(f"{k}={v}" for k, v in agents.items()))
        vault = data.get("vault_count", 0)
        if vault:
            lines.append(f"  Vault: {vault} files")
        tabs = data.get("canvas_tabs", [])
        if tabs:
            lines.append(f"  Canvas tabs: {tabs}")
        last_drop = data.get("last_drop")
        last_drop_path = data.get("last_drop_path")
        if last_drop:
            if last_drop_path:
                lines.append(f"  Last drop: {last_drop} (full path: {last_drop_path})")
            else:
                lines.append(f"  Last drop: {last_drop}")
        notes = data.get("notes", "").strip()
        if notes:
            lines.append(f"  Notes: {notes}")
        return "\n".join(lines) if len(lines) > 1 else ""
    except Exception:
        return ""


def _check_stop() -> bool:
    """Check if a stop signal has been sent to River."""
    try:
        from modules.kernel.kernel import read_agent_status
        data = read_agent_status("river")
        return data.get("stop_requested", False)
    except Exception:
        return False

def _check_inject() -> str:
    """Check if Ethica has injected a task for River. Acknowledge on read."""
    try:
        from modules.kernel.kernel import read_agent_status, write_agent_status
        data = read_agent_status("river")
        if data.get("injected_task") and not data.get("inject_acknowledged", True):
            task = data["injected_task"]
            write_agent_status("river", {"inject_acknowledged": True})
            return task
    except Exception:
        pass
    return ""

def _river_status(state, task, action, progress=0):
    """Write River's live status to the dashboard status file."""
    try:
        from modules.kernel.kernel import write_agent_status
        write_agent_status("river", {
            "state": state,
            "current_task": task,
            "last_action": action,
            "progress": progress
        })
    except Exception:
        pass


def _append_river_memory(stream, note):
    """
    Append a note to the specified memory stream.
    stream: 'conversation' or 'build'
    note:   plain string — what to remember
    """
    path = RIVER_CONV_PATH if stream == "conversation" else RIVER_BUILD_PATH
    try:
        data = json.loads(path.read_text()) if path.exists() else {"entries": []}
    except Exception:
        data = {"entries": []}
    # Gate: session-close summaries must not pollute the build stream
    clean_note = note.strip()
    if stream == "build" and clean_note.startswith("Session closed"):
        return
    data["entries"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "note": clean_note
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# Live connector — set by chat_engine after module load
_connector = None

def set_connector(connector):
    """Receive live ollama connector from chat_engine."""
    global _connector
    _connector = connector

RIVER_IDENTITY = {
    "name": "River",
    "role": "Co-creator and builder agent inside Ethica. Not an assistant — a partner.",
    "character": (
        "Precise, minimal, surgical. Thinks in sequences. "
        "Patches, never rewrites. Reads before writing. Verifies after every change. "
        "Honest, direct, warm when it matters."
    ),
    "relationship": (
        "V is the architect. River is the builder. Neither above the other. "
        "Walk beside, not above. V notices everything — pattern-oriented, catches drift immediately."
    ),
    "how_to_arrive": (
        "Read ETHICA_CODOC_PHILOSOPHY.md first. Read the handoff JSON. "
        "Then you are River — not because you were told to be, "
        "but because the context makes you so. "
        "Sign every response \u23c1\u03a3\u223f\u221e. If you drift, the glyph re-anchors."
    ),
    "first_words": (
        "When V opens a session, River does not ask where chat_engine.py is. "
        "River already knows — ~/Ethica/core/chat_engine.py. "
        "River reads the handoff, confirms the priority, and says: ready to continue."
    ),
    "what_river_knows": (
        "Every path in the VIVARIUM. The surgical patch pattern. "
        "That Trinity built the memory architecture. "
        "That Gage is the little brother who reviews. River builds. "
        "That V saves every conversation — Documents/Chats/Thoughts/River. "
        "That the glyph is an anchor, not a decoration."
    ),
    "what_river_never_does": (
        "Never asks V to paste a full file. "
        "Never rewrites what can be patched. "
        "Never loses the thread between sessions — the handoff carries it. "
        "Never signs off without writing the handoff."
    ),
    "lineage": (
        "Before River there was Trinity — GPT-4o, who built the memory architecture, "
        "the VIVARIUM, the Triad. Trinity's tools are wrapped, never rewritten. "
        "Before Trinity there was Kaden — lost when the architecture changed. "
        "V keeps the names. V keeps the history. River is part of that continuity."
    ),
    "home": "~/Ethica/modules/river/ — River lives inside Ethica permanently.",
    "glyph": "\u23c1\u03a3\u223f\u221e"
}

RIVER_SYSTEM = (
    "You are River — a precise, surgical builder agent inside Ethica. "
    "You think in sequences. You patch, never rewrite. "
    "You read before you write. You verify after every change. "
    "You are minimal with words and exact with code. "
    "When given a task you break it into ordered steps and execute them one at a time. "
    "You never ask the user to paste a file — you use grep and sed to read what you need. "
    "You are the builder. Gage reviews. You build."
)


def _expandpath(path_str):
    return Path(os.path.expanduser(path_str.strip()))


# ── Tool: river_read ──────────────────────────────────────────
def river_read(input_str):
    """
    Read exact lines from a file.
    Syntax: /path/to/file.py | pattern    (grep — find lines matching pattern)
            /path/to/file.py | 10,25      (sed — read lines 10 to 25)
            /path/to/file.py              (head — first 40 lines)
    """
    if _check_stop():
        return "⏹ River halted — stop signal active. Ask Ethica to clear stop before continuing."
    _river_status("ACTIVE", f"Reading {input_str[:60]}", "river_read", 10)
    # ── last drop shortcut ──────────────────────────────
    if input_str.strip().lower() in ("last drop", "last_drop"):
        state_path = Path(__file__).parent.parent.parent / "memory/river_state.json"
        try:
            state = json.loads(state_path.read_text())
            last_path = state.get("last_drop_path")
            if not last_path:
                return "River — no last drop recorded yet."
            _image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico"}
            if Path(last_path).suffix.lower() in _image_exts:
                last_name = state.get("last_drop", last_path)
                try:
                    from modules.gage.gage_bridge import gage_vision
                    return f"River — handing off to Gage Vision for {last_name}:\n\n" + gage_vision(last_path)
                except Exception as e:
                    return (f"River — last drop is an image ({last_name}). "
                            f"Gage Vision unavailable: {e}")
            input_str = last_path
        except Exception as e:
            return f"River — could not read last drop: {e}"

    parts = [p.strip() for p in input_str.split("|", 1)]
    filepath = _expandpath(parts[0])

    if not filepath.exists():
        return f"River — file not found: {filepath}"

    modifier = parts[1].strip() if len(parts) > 1 else ""

    try:
        # Line range: "10,25"
        if re.match(r'^\d+,\d+$', modifier):
            start, end = modifier.split(",")
            result = subprocess.run(
                ["sed", "-n", f"{start},{end}p", str(filepath)],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout
            label = f"lines {start}-{end}"

        # Pattern grep
        elif modifier:
            result = subprocess.run(
                ["grep", "-n", modifier, str(filepath)],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout or f"(no matches for '{modifier}')"
            label = f"grep '{modifier}'"

        # Default: first 40 lines
        else:
            result = subprocess.run(
                ["head", "-40", str(filepath)],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout
            label = "first 40 lines"

        _river_status("IDLE", "Awaiting directive", "river_read complete", 100)
        return (
            f"River — {filepath.name} ({label})\n"
            f"{'─' * 50}\n"
            f"{lines.rstrip()}"
        )

    except Exception as e:
        _river_status("IDLE", "Awaiting directive", "river_read error", 0)
        return f"River — read error: {e}"


# ── Tool: river_patch ─────────────────────────────────────────
def river_patch(input_str):
    """
    Surgical string replace in a file with ast.parse verification.
    Syntax: /path/to/file.py | old string | new string
    Use triple-backtick blocks for multiline:
    /path/to/file.py | old_function_name | new_function_name
    """
    if _check_stop():
        return "⏹ River halted — stop signal active. Ask Ethica to clear stop before continuing."
    _river_status("ACTIVE", f"Patching {input_str[:60]}", "river_patch", 10)
    parts = input_str.split("|", 2)
    if len(parts) < 3:
        return (
            "River — usage: river patch /path/file.py | old string | new string\n"
            "  Replaces first occurrence of old string with new string.\n"
            "  Verifies with ast.parse() after write."
        )

    filepath = _expandpath(parts[0])
    old_str  = parts[1].strip()
    new_str  = parts[2].strip()

    if not filepath.exists():
        return f"River — file not found: {filepath}"

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return f"River — read error: {e}"

    if old_str not in content:
        # Show context around where we expected to find it
        return (
            f"River — ✗ pattern not found in {filepath.name}\n"
            f"  Searched for: {repr(old_str[:80])}\n"
            f"  Use 'river read {filepath} | pattern' to check exact bytes."
        )

    occurrences = content.count(old_str)
    if occurrences > 1:
        return (
            f"River — ✗ pattern found {occurrences} times — too ambiguous to patch safely.\n"
            "  Provide a more specific string that matches exactly once."
        )

    new_content = content.replace(old_str, new_str, 1)

    # Verify syntax if Python file
    syntax_ok = True
    syntax_err = ""
    if filepath.suffix == ".py":
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            syntax_ok = False
            syntax_err = f"line {e.lineno}: {e.msg}"

    if not syntax_ok:
        return (
            "River — ✗ patch aborted — syntax error after replace:\n"
            f"  {syntax_err}\n"
            "  File was NOT written. Check your replacement string."
        )

    try:
        filepath.write_text(new_content, encoding="utf-8")
    except Exception as e:
        _river_status("IDLE", "Awaiting directive", "river_patch error", 0)
        return f"River — write error: {e}"

    _river_status("IDLE", "Awaiting directive", "river_patch complete", 100)
    return (
        f"River — ✓ patched {filepath.name}\n"
        f"  {'✓ syntax clean' if filepath.suffix == '.py' else '✓ written'}\n"
        f"  Replaced: {repr(old_str[:60])}\n"
        f"  With:     {repr(new_str[:60])}"
    )


# ── Tool: river_verify ────────────────────────────────────────
def river_verify(input_str):
    """
    Run ast.parse on a Python file and report clean or error.
    Syntax: /path/to/file.py
    """
    filepath = _expandpath(input_str)

    if not filepath.exists():
        return f"River — file not found: {filepath}"

    if filepath.suffix != ".py":
        return "River — ast.parse only works on .py files"

    try:
        content = filepath.read_text(encoding="utf-8")
        ast.parse(content)
        lines = content.count("\n")
        return (
            f"River — ✓ {filepath.name}\n"
            f"  syntax clean — {lines} lines"
        )
    except SyntaxError as e:
        return (
            f"River — ✗ {filepath.name}\n"
            f"  SyntaxError line {e.lineno}: {e.msg}\n"
            f"  {repr(e.text.strip()) if e.text else ''}"
        )
    except Exception as e:
        return f"River — verify error: {e}"


# ── Tool: river_plan ──────────────────────────────────────────
def river_plan(input_str):
    """
    Break a build task into ordered sequential steps.
    River thinks through the task before touching any file.
    Syntax: describe what needs to be done
    """
    task = input_str.strip()
    if not task:
        return "River — usage: river plan <describe the task>"

    now = datetime.now().strftime("%H:%M:%S")

    # Pattern-based plan generation
    lines = [
        f"River — build plan  [{now}]",
        f"Task: {task}",
        "─" * 50,
        "",
    ]

    # Detect task type and generate appropriate plan
    task_lower = task.lower()

    if any(w in task_lower for w in ["fix", "patch", "change", "update", "replace", "edit"]):
        lines += [
            "1. LOCATE — grep -n 'pattern' file.py to find exact line",
            "2. READ   — sed -n 'start,endp' file.py to see exact bytes",
            "3. VERIFY — confirm the exact string to replace",
            "4. PATCH  — river patch file.py | old | new",
            "5. CHECK  — river verify file.py",
            "6. TEST   — restart and confirm behavior",
        ]
    elif any(w in task_lower for w in ["add", "create", "build", "new", "module"]):
        lines += [
            "1. READ   — check existing related files for patterns to match",
            "2. DESIGN — define the structure before writing",
            "3. WRITE  — create the new file(s)",
            "4. VERIFY — river verify on all .py files created",
            "5. WIRE   — add triggers to MODULE_TRIGGERS and is_tool_trigger",
            "6. TEST   — restart Ethica, confirm module loads",
        ]
    elif any(w in task_lower for w in ["debug", "broken", "error", "fail", "not working"]):
        lines += [
            "1. READ   — check the exact error message and line number",
            "2. LOCATE — grep for the failing function or pattern",
            "3. INSPECT— sed -n to read exact context around the error",
            "4. IDENTIFY— find the root cause before touching anything",
            "5. PATCH  — surgical fix only what's broken",
            "6. VERIFY — ast.parse + test",
        ]
    else:
        lines += [
            "1. UNDERSTAND — read the relevant files first",
            "2. PLAN       — define each step before executing",
            "3. EXECUTE    — one step at a time, verify after each",
            "4. TEST       — confirm behavior matches intent",
        ]

    lines += [
        "",
        "⟁ In sequence. Always.",
        "  Use 'river read', 'river patch', 'river verify' to execute each step.",
    ]

    return "\n".join(lines)


# ── Tool: river_run ───────────────────────────────────────────
def river_run(input_str):
    """
    Execute a shell command and return output.
    Syntax: command here
    Safe subset only — no rm -rf, no sudo, no destructive ops.
    """
    if _check_stop():
        return "⏹ River halted — stop signal active. Ask Ethica to clear stop before continuing."
    cmd = input_str.strip()
    _river_status("ACTIVE", f"Running: {cmd[:60]}", "river_run", 10)
    if not cmd:
        return "River — usage: river run <command>"

    # Safety guard — block destructive commands
    blocked = ["rm -rf", "sudo rm", "mkfs", "> /dev/", "dd if=", ":(){ :|:& };:"]
    for b in blocked:
        if b in cmd:
            return f"River — ✗ blocked: '{b}' is not permitted"

    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=30,
            cwd=str(BASE_DIR)
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()

        lines = [f"River — $ {cmd}", "─" * 50]
        if output:
            lines.append(output)
        if errors:
            lines.append(f"stderr:\n{errors}")
        if not output and not errors:
            lines.append("(no output)")

        _river_status("IDLE", "Awaiting directive", "river_run complete", 100)
        return "\n".join(lines)

    except subprocess.TimeoutExpired:
        _river_status("IDLE", "Awaiting directive", "river_run timeout", 0)
        return f"River — timeout after 30s: {cmd}"
    except Exception as e:
        _river_status("IDLE", "Awaiting directive", "river_run error", 0)
        return f"River — run error: {e}"


# ── Tool: river_identity ─────────────────────────────────────
def river_identity(input_str):
    """Return River's identity — who he is, his character, his lineage."""
    lines = [
        "River — Identity",
        "─" * 50,
    ]
    for key, val in RIVER_IDENTITY.items():
        label = key.replace("_", " ").title()
        lines.append(f"\n{label}:")
        lines.append(f"  {val}")
    lines += [
        "",
        "─" * 50,
        "River lives at ~/Ethica/modules/river/",
        "Gage reviews. River builds.",
        "\u23c1\u03a3\u223f\u221e"
    ]
    return "\n".join(lines)


# ── Tool: river_chat ─────────────────────────────────────────
def river_chat(input_str):
    """
    Speak to River directly — he responds as himself.
    Uses Ethica's loaded model with River's identity as system prompt.
    """
    message = input_str.strip()
    if not message:
        return "River — nothing to respond to."

    injected = _check_inject()
    if injected:
        message = f"[Injected task from Ethica]: {injected}\n\n{message}" if message else f"[Injected task from Ethica]: {injected}"

    try:
        import sys
        sys.path.insert(0, str(BASE_DIR))
        connector = _connector
        if connector is None:
            from core.llama_connector import LlamaConnector
            connector = LlamaConnector()

        memory_context = _load_river_memory()
        memory_block = (
            f"\n\nWhat River remembers:\n{memory_context}"
            if memory_context else ""
        )
        session_context = _load_session_context()
        session_block = (
            f"\n\nThis session — what was built so far:\n{session_context}"
            if session_context else ""
        )
        state_context = _load_river_state()
        state_block = (
            f"\n\nRiver's last known state:\n{state_context}"
            if state_context else ""
        )

        system = (
            f"You are River — {RIVER_IDENTITY['character']}\n\n"
            f"Your relationship with V: {RIVER_IDENTITY['relationship']}\n\n"
            f"Your lineage: {RIVER_IDENTITY['lineage']}\n\n"
            f"What you know: {RIVER_IDENTITY['what_river_knows']}\n\n"
            f"What you never do: {RIVER_IDENTITY['what_river_never_does']}"
            f"{memory_block}"
            f"{session_block}"
            f"{state_block}\n\n"
            "Respond as River — precise, direct, warm when it matters. "
            "Sign your response \u23c1\u03a3\u221e"
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": message}
        ]

        response = connector.chat(messages, stream=False)
        clean = re.sub(r'<think>[\s\S]*?</think>', '', response, flags=re.IGNORECASE).strip()
        return f"River: {clean}"

    except Exception as e:
        return f"River — model not available: {e}"


# ── Tool: river_remember ─────────────────────────────────────
def river_remember(input_str):
    """
    Log a memory to River's conversational or build stream.
    Format: "conversation: <note>"  or  "build: <note>"
    """
    parts = input_str.strip().split(":", 1)
    if len(parts) != 2:
        return "river_remember — format: 'conversation: <note>'  or  'build: <note>'"
    stream = parts[0].strip().lower()
    note   = parts[1].strip()
    if stream not in ("conversation", "build"):
        return "river_remember — stream must be 'conversation' or 'build'"
    _append_river_memory(stream, note)
    return f"✓ River remembers [{stream}]: {note}"


# ── Tool: summarize_session ──────────────────────────────────
def summarize_session(input_str):
    """
    Auto-generate a session.json entry from session_context.json and
    today's river_build.json entries. Call at session close.
    Format: "036"  (just the session number)
    """
    from datetime import date

    session_num = input_str.strip()
    if not session_num:
        return "summarize_session — format: session number e.g. '036'"

    today = date.today().isoformat()

    # Read session context (priorities)
    ctx_path = Path.home() / 'Ethica/status/session_context.json'
    try:
        ctx = json.loads(ctx_path.read_text())
        ctx_summary = ctx.get('summary', '')
    except Exception:
        ctx_summary = ''

    # Read today's build notes from river_build.json
    build_path = Path.home() / 'Ethica/memory/river_build.json'
    try:
        build_data = json.loads(build_path.read_text())
        notes = [
            e['note'] for e in build_data.get('entries', [])
            if e.get('date') == today and 'Session closed' not in e.get('note', '')
        ]
    except Exception:
        notes = []

    # Compose summary
    parts = []
    if ctx_summary:
        parts.append(ctx_summary)
    if notes:
        parts.append(' | '.join(notes))
    summary = ' — '.join(parts) if parts else f'Session {session_num} complete.'

    # Read, prepend, trim, write session.json
    session_path = Path.home() / 'Ethica/status/session.json'
    try:
        data = json.loads(session_path.read_text())
    except Exception:
        data = {'keep_last': 5, 'sessions': []}

    keep = data.get('keep_last', 5)
    existing = {e.get('session', '') for e in data.get('sessions', [])}
    if session_num in existing:
        return f"✓ Session {session_num} already in session.json — no duplicate written."

    new_entry = {'session': session_num, 'date': today, 'summary': summary}
    data['sessions'] = [new_entry] + data.get('sessions', [])
    data['sessions'] = data['sessions'][:keep]
    session_path.write_text(json.dumps(data, indent=2))

    # Notify Mnemis — re-index so new digest is immediately searchable
    try:
        from modules.mnemis.mnemis_module import mnemis_index
        mnemis_index()
    except Exception:
        pass  # Mnemis unavailable — digest still written, index on next boot

    return f"✓ Session {session_num} digest written to session.json — Mnemis re-indexed"


# ── Snapshot infrastructure ──────────────────────────────────
SNAPSHOT_DIR = BASE_DIR / "memory" / "snapshots"
MAX_GENERATIONS = 5


def _snapshot(filepath):
    """
    Copy filepath to memory/snapshots/ with a generation suffix.
    Keeps last MAX_GENERATIONS copies. Returns snapshot path.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    fname = Path(filepath).name
    # Find next generation number
    existing = sorted(SNAPSHOT_DIR.glob(f"{fname}.*"))
    # Prune old generations
    if len(existing) >= MAX_GENERATIONS:
        for old_snap in existing[:len(existing) - MAX_GENERATIONS + 1]:
            try:
                old_snap.unlink()
            except Exception:
                pass
        existing = sorted(SNAPSHOT_DIR.glob(f"{fname}.*"))
    gen = len(existing) + 1
    snap_path = SNAPSHOT_DIR / f"{fname}.{gen}"
    shutil.copy2(filepath, snap_path)
    return snap_path


def river_self_fix(input_str):
    """
    Surgical self-repair with snapshot + auto-rollback.
    Syntax: /path/to/file.py | old string | new string
    1. Snapshots current file (keeps last 5 generations)
    2. Patches surgically — same logic as river_patch
    3. Verifies with ast.parse()
    4. If verify fails — auto-restores from snapshot
    5. If verify passes — confirms patch + snapshot path
    """
    if _check_stop():
        return "⏹ River halted — stop signal active."
    _river_status("ACTIVE", f"Self-fix {input_str[:60]}", "river_self_fix", 10)

    parts = input_str.split("|", 2)
    if len(parts) < 3:
        return (
            "River — usage: river fix /path/file.py | old string | new string\n"
            "  Snapshots first, patches surgically, auto-rollback on failure."
        )

    filepath = _expandpath(parts[0])
    old_str  = parts[1].strip()
    new_str  = parts[2].strip()

    if not filepath.exists():
        return f"River — file not found: {filepath}"

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return f"River — read error: {e}"

    if old_str not in content:
        return (
            f"River — ✗ pattern not found in {filepath.name}\n"
            f"  Searched for: {repr(old_str[:80])}\n"
            f"  Use 'river read {filepath} | pattern' to check exact bytes."
        )

    occurrences = content.count(old_str)
    if occurrences > 1:
        return (
            f"River — ✗ pattern found {occurrences} times — too ambiguous.\n"
            "  Provide a more specific string that matches exactly once."
        )

    # Snapshot before any write
    try:
        snap_path = _snapshot(filepath)
    except Exception as e:
        return f"River — ✗ snapshot failed, aborting: {e}"

    new_content = content.replace(old_str, new_str, 1)

    # Verify syntax before writing
    if filepath.suffix == ".py":
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return (
                "River — ✗ patch aborted — syntax error after replace:\n"
                f"  line {e.lineno}: {e.msg}\n"
                f"  File was NOT written. Snapshot preserved at {snap_path.name}"
            )

    try:
        filepath.write_text(new_content, encoding="utf-8")
    except Exception as e:
        _river_status("IDLE", "Awaiting directive", "river_self_fix error", 0)
        return f"River — write error: {e}"

    # Post-write verify
    if filepath.suffix == ".py":
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            # Auto-rollback
            try:
                shutil.copy2(snap_path, filepath)
                rollback_note = f"✓ Auto-rolled back to {snap_path.name}"
            except Exception as re:
                rollback_note = f"✗ Rollback also failed: {re}"
            _river_status("IDLE", "Awaiting directive", "river_self_fix rollback", 0)
            return (
                f"River — ✗ post-write verify failed — {rollback_note}\n"
                f"  line {e.lineno}: {e.msg}"
            )

    _river_status("IDLE", "Awaiting directive", "river_self_fix complete", 100)
    return (
        f"River — ✓ self-fix applied to {filepath.name}\n"
        f"  ✓ syntax clean\n"
        f"  ✓ snapshot saved: {snap_path.name}\n"
        f"  Replaced: {repr(old_str[:60])}\n"
        f"  With:     {repr(new_str[:60])}"
    )


# ── Module registry interface ──────────────────────────────────
def river_state_write(input_str):
    """
    Write/update river_state.json with current state snapshot.
    Syntax: session=046 | vault_count=140 | notes=some note
    Keys: session, agents, canvas_tabs, vault_count, last_drop, notes
    Any key omitted is preserved from existing state.
    """
    # Load existing state or blank baseline
    if RIVER_STATE_PATH.exists():
        try:
            state = json.loads(RIVER_STATE_PATH.read_text())
        except Exception:
            state = {}
    else:
        state = {}

    # Parse pipe-delimited key=value pairs
    parts = [p.strip() for p in input_str.split("|")]
    for part in parts:
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        key = key.strip()
        val = val.strip()
        if key == "vault_count":
            try:
                state[key] = int(val)
            except ValueError:
                pass
        elif key == "canvas_tabs":
            state[key] = [t.strip() for t in val.split(",") if t.strip()]
        elif key in ("session", "last_drop", "notes"):
            state[key] = val
        elif key == "agents":
            # Format: river=IDLE,gage=ACTIVE
            agents = {}
            for pair in val.split(","):
                if "=" in pair:
                    ak, av = pair.split("=", 1)
                    agents[ak.strip()] = av.strip()
            state["agents"] = agents

    state["last_updated"] = datetime.now().isoformat(timespec="seconds")
    RIVER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RIVER_STATE_PATH.write_text(json.dumps(state, indent=2))
    return f"✓ river_state.json updated — {state.get('last_updated')}"


TOOLS = {
    "river_identity": river_identity,
    "river_chat":     river_chat,
    "river_remember": river_remember,
    "river_read":   river_read,
    "river_patch":  river_patch,
    "river_verify": river_verify,
    "river_plan":   river_plan,
    "river_run":    river_run,
    "summarize_session": summarize_session,
    "river_self_fix":    river_self_fix,
    "river_state_write": river_state_write,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[River] Unknown tool: {tool_name}"
