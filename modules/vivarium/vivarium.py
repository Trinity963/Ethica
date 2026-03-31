# ============================================================
# Ethica v0.1 — vivarium.py
# VIVARIUM Heartbeat Dashboard — sovereign process monitor
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Discovers what the user is running — nothing hardcoded.
# Reads ~/Ethica/memory/vivarium_watch.json for custom labels.
# Pushes live snapshot to Canvas VIVARIUM tab.
# ============================================================

import json
import threading
import time
from datetime import datetime
from pathlib import Path

import psutil

MODULE_DIR  = Path(__file__).parent
WATCH_FILE  = Path.home() / "Ethica" / "memory" / "vivarium_watch.json"

# ── Default discovery patterns (generic, no personal stack) ──
DEFAULT_PATTERNS = [
    "python3", "python", "ollama", "streamlit",
    "electron", "node", "uvicorn", "fastapi",
    "flask", "gradio", "jupyter", "llama",
]

# ── Auto-refresh state ────────────────────────────────────────
_refresh_thread  = None
_refresh_running = False
_refresh_interval = 10  # seconds
_canvas_ref      = None  # set by vivarium_start


def _load_watch_config():
    """Load user watch config if present. Returns list of {label, pattern} dicts."""
    if WATCH_FILE.exists():
        try:
            data = json.loads(WATCH_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def _discover_processes(patterns):
    """Find running processes matching any pattern. Returns list of dicts."""
    found = []
    seen_pids = set()
    for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent',
                                   'memory_info', 'create_time', 'cmdline']):
        try:
            info   = p.info
            name   = (info['name'] or "").lower()
            cmd    = " ".join(info['cmdline'] or []).lower()
            pid    = info['pid']
            if pid in seen_pids:
                continue
            for pat in patterns:
                if pat.lower() in name or pat.lower() in cmd:
                    uptime_s = time.time() - (info['create_time'] or time.time())
                    mem_mb   = round(info['memory_info'].rss / 1024 / 1024, 1) if info['memory_info'] else 0.0
                    found.append({
                        "pid":    pid,
                        "name":   info['name'] or "?",
                        "status": info['status'] or "?",
                        "mem_mb": mem_mb,
                        "uptime": uptime_s,
                        "match":  pat,
                    })
                    seen_pids.add(pid)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found


def _format_uptime(seconds):
    seconds = int(seconds)
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _build_snapshot():
    """Build heartbeat snapshot string."""
    now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config   = _load_watch_config()

    # Merge user patterns with defaults
    patterns = list(DEFAULT_PATTERNS)
    label_map = {}
    for entry in config:
        pat = entry.get("pattern", "")
        lbl = entry.get("label", pat)
        if pat and pat not in patterns:
            patterns.append(pat)
        if pat:
            label_map[pat] = lbl

    procs = _discover_processes(patterns)

    # System stats
    cpu_pct = psutil.cpu_percent(interval=0.2)
    ram     = psutil.virtual_memory()
    ram_pct = ram.percent
    ram_used = round(ram.used / 1024 / 1024 / 1024, 2)
    ram_total = round(ram.total / 1024 / 1024 / 1024, 2)

    lines = [
        "⟁ VIVARIUM — Heartbeat",
        f"  {now}",
        "─" * 50,
        f"  CPU : {cpu_pct:.1f}%",
        f"  RAM : {ram_used} / {ram_total} GB  ({ram_pct:.1f}%)",
        "─" * 50,
    ]

    if not procs:
        lines.append("  No matching processes discovered.")
        lines.append("")
        lines.append("  Add ~/Ethica/memory/vivarium_watch.json")
        lines.append('  [{"label": "MyApp", "pattern": "myapp"}]')
    else:
        lines.append(f"  {'PID':<8} {'NAME':<22} {'MEM MB':<9} {'UPTIME':<10} STATUS")
        lines.append("  " + "─" * 58)
        for p in sorted(procs, key=lambda x: x['mem_mb'], reverse=True):
            label = label_map.get(p['match'], p['name'])
            lines.append(
                f"  {p['pid']:<8} {label[:21]:<22} {p['mem_mb']:<9} "
                f"{_format_uptime(p['uptime']):<10} {p['status']}"
            )

    lines += [
        "─" * 50,
        f"  {len(procs)} process(es) active",
        f"  Auto-refresh: {'ON  (' + str(_refresh_interval) + 's)' if _refresh_running else 'OFF'}",
    ]
    return "\n".join(lines)


def _push_to_canvas():
    """Push current snapshot to Canvas VIVARIUM tab."""
    global _canvas_ref
    if _canvas_ref is None:
        return False
    try:
        snapshot = _build_snapshot()
        _canvas_ref.push_debug_from_ethica(snapshot, tab_name="VIVARIUM", lang=None)
        return True
    except Exception:
        return False


def _refresh_loop():
    global _refresh_running
    while _refresh_running:
        _push_to_canvas()
        time.sleep(_refresh_interval)


# ── Tool: vivarium_status ─────────────────────────────────────
def vivarium_status(input_str):
    """Take a snapshot and push to Canvas VIVARIUM tab via DEBUG marker."""
    snapshot = _build_snapshot()
    now = datetime.now().strftime("%H:%M:%S")
    # Return brief Ops summary + DEBUG marker to push full snapshot to Canvas
    return f"VIVARIUM — heartbeat {now}\n→ Full snapshot in Canvas VIVARIUM tab\n[DEBUG:VIVARIUM::\n{snapshot}\n]"


# ── Tool: vivarium_start ──────────────────────────────────────
def vivarium_start(input_str):
    """Start auto-refresh. Optional interval in seconds: 'vivarium start 30'"""
    global _refresh_thread, _refresh_running, _refresh_interval

    # Parse optional interval
    try:
        secs = int(input_str.strip())
        if 5 <= secs <= 300:
            _refresh_interval = secs
    except (ValueError, TypeError):
        pass

    if _refresh_running:
        return f"VIVARIUM — auto-refresh already running (every {_refresh_interval}s)"

    _refresh_running = True
    _refresh_thread  = threading.Thread(target=_refresh_loop, daemon=True)
    _refresh_thread.start()
    return f"VIVARIUM — auto-refresh started (every {_refresh_interval}s)\n→ Canvas VIVARIUM tab will update automatically"


# ── Tool: vivarium_stop ───────────────────────────────────────
def vivarium_stop(input_str):
    """Stop auto-refresh."""
    global _refresh_running
    if not _refresh_running:
        return "VIVARIUM — auto-refresh is not running"
    _refresh_running = False
    return "VIVARIUM — auto-refresh stopped"


# ── Tool: vivarium_watch ──────────────────────────────────────
def vivarium_watch(input_str):
    """Show or set the watch config. Input: 'show' or 'label=MyApp pattern=myapp'"""
    cmd = input_str.strip().lower()

    if not cmd or cmd == "show":
        config = _load_watch_config()
        if not config:
            lines = [
                "VIVARIUM — watch config",
                "─" * 40,
                "No custom config found.",
                f"Create: {WATCH_FILE}",
                "",
                "Format:",
                '[{"label": "MyApp", "pattern": "myapp"},',
                ' {"label": "API",   "pattern": "uvicorn"}]',
            ]
        else:
            lines = ["VIVARIUM — watch config", "─" * 40]
            for entry in config:
                lines.append(f"  {entry.get('label','?'):<20} → {entry.get('pattern','?')}")
        return "\n".join(lines)

    # Parse label=X pattern=Y
    try:
        parts  = dict(p.split("=", 1) for p in input_str.strip().split() if "=" in p)
        label  = parts.get("label", "").strip()
        pattern = parts.get("pattern", "").strip()
        if not label or not pattern:
            return "VIVARIUM — usage: vivarium watch label=MyApp pattern=myapp"

        config = _load_watch_config()
        # Update or append
        updated = False
        for entry in config:
            if entry.get("pattern") == pattern:
                entry["label"] = label
                updated = True
                break
        if not updated:
            config.append({"label": label, "pattern": pattern})

        WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
        WATCH_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
        return f"VIVARIUM — watch config updated\n  {label} → {pattern}"
    except Exception as e:
        return f"VIVARIUM — watch error: {e}"


# ── Canvas injection (called by chat_engine after canvas init) ─
def set_canvas(canvas):
    global _canvas_ref
    _canvas_ref = canvas


# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "vivarium_status": vivarium_status,
    "vivarium_start":  vivarium_start,
    "vivarium_stop":   vivarium_stop,
    "vivarium_watch":  vivarium_watch,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[VIVARIUM] Unknown tool: {tool_name}"
