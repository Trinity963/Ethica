# ============================================================
# Ethica — CrashReporter Module
# Global exception handler, crash logger, startup reporter.
# Architect: Victory  |  Build Partner: River
# ⟁Σ∿∞
# ============================================================

import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parents[2]
CRASH_DIR  = BASE_DIR / "memory" / "crashes"
CONV_LOG   = BASE_DIR / "memory" / "conversation_log.json"
MAX_CRASHES = 20


def _ensure_crash_dir():
    CRASH_DIR.mkdir(parents=True, exist_ok=True)


def _last_actions(n=10):
    try:
        if not CONV_LOG.exists():
            return []
        with open(CONV_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            entries = data[-n:]
        elif isinstance(data, dict):
            entries = list(data.values())[-n:]
        else:
            return []
        out = []
        for e in entries:
            if isinstance(e, dict):
                role = e.get("role", "?")
                content = str(e.get("content", ""))[:120]
                out.append(f"[{role}] {content}")
            else:
                out.append(str(e)[:120])
        return out
    except Exception:
        return []


def _write_crash(exc_type, exc_value, exc_tb):
    _ensure_crash_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "exception_type": exc_type.__name__ if exc_type else "Unknown",
        "message": str(exc_value),
        "traceback": tb_str,
        "last_actions": _last_actions(10),
    }
    crash_file = CRASH_DIR / f"crash_{timestamp}.json"
    with open(crash_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    files = sorted(CRASH_DIR.glob("crash_*.json"))
    if len(files) > MAX_CRASHES:
        for old in files[:-MAX_CRASHES]:
            try:
                old.unlink()
            except Exception:
                pass
    return crash_file


def _latest_crash():
    _ensure_crash_dir()
    files = sorted(CRASH_DIR.glob("crash_*.json"))
    return files[-1] if files else None


def _load_crash(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def install_excepthook():
    def _handler(exc_type, exc_value, exc_tb):
        try:
            _write_crash(exc_type, exc_value, exc_tb)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _handler


def check_crash_log(root):
    latest = _latest_crash()
    if not latest:
        return
    try:
        data = _load_crash(latest)
    except Exception:
        return

    import tkinter as tk
    from tkinter import scrolledtext

    popup = tk.Toplevel(root)
    popup.title("⚠ Ethica — Crash Report")
    popup.geometry("720x500")
    popup.configure(bg="#1a1a2e")
    popup.lift()
    popup.focus_force()

    tk.Label(
        popup,
        text=f"⚠  Ethica crashed at {data.get('timestamp','unknown')}",
        bg="#1a1a2e", fg="#f87171",
        font=("Helvetica", 13, "bold"),
        anchor="w", padx=16, pady=10,
    ).pack(fill="x")

    tk.Label(
        popup,
        text=f"Exception: {data.get('exception_type','?')} — {data.get('message','')}",
        bg="#1a1a2e", fg="#fbbf24",
        font=("Helvetica", 10),
        anchor="w", padx=16,
    ).pack(fill="x")

    tk.Frame(popup, bg="#333355", height=1).pack(fill="x", padx=16, pady=6)

    tk.Label(popup, text="Traceback:", bg="#1a1a2e", fg="#a0a0c0",
             font=("Helvetica", 9, "bold"), anchor="w", padx=16).pack(fill="x")

    tb_box = scrolledtext.ScrolledText(
        popup, bg="#0f0f1e", fg="#e0e0f0",
        font=("Courier", 9), height=12,
        relief="flat", bd=0, padx=8, pady=8,
    )
    tb_box.pack(fill="both", expand=True, padx=16, pady=(0, 4))
    tb_box.insert("end", data.get("traceback", "No traceback recorded."))
    tb_box.config(state="disabled")

    actions = data.get("last_actions", [])
    if actions:
        tk.Label(popup, text="Last actions before crash:",
                 bg="#1a1a2e", fg="#a0a0c0",
                 font=("Helvetica", 9, "bold"), anchor="w", padx=16).pack(fill="x")
        act_box = tk.Text(
            popup, bg="#0f0f1e", fg="#c0c0e0",
            font=("Courier", 9), height=5,
            relief="flat", bd=0, padx=8, pady=4,
        )
        act_box.pack(fill="x", padx=16, pady=(0, 4))
        act_box.insert("end", "\n".join(actions))
        act_box.config(state="disabled")

    btn_frame = tk.Frame(popup, bg="#1a1a2e")
    btn_frame.pack(fill="x", padx=16, pady=8)

    def _clear_and_close():
        try:
            latest.unlink()
        except Exception:
            pass
        popup.destroy()

    tk.Button(
        btn_frame, text="Clear & Close",
        bg="#333355", fg="#e0e0f0",
        font=("Helvetica", 10), relief="flat",
        padx=12, pady=4,
        command=_clear_and_close,
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btn_frame, text="Keep & Close",
        bg="#1a1a2e", fg="#808090",
        font=("Helvetica", 10), relief="flat",
        padx=12, pady=4,
        command=popup.destroy,
    ).pack(side="left")


def crash_status(input_str=""):
    _ensure_crash_dir()
    files = sorted(CRASH_DIR.glob("crash_*.json"))
    if not files:
        return "✓ No crash logs found. Ethica has been stable."
    lines = [f"⚠ {len(files)} crash log(s) on record:\n"]
    for f in files[-5:]:
        try:
            data = _load_crash(f)
            lines.append(
                f"  {data['timestamp']} — {data['exception_type']}: {data['message'][:80]}"
            )
        except Exception:
            lines.append(f"  {f.name} — (unreadable)")
    if len(files) > 5:
        lines.append(f"  ... and {len(files)-5} older entries.")
    lines.append(f"\nMost recent: {files[-1].name}")
    lines.append("Use 'crash log' to read the full traceback.")
    return "\n".join(lines)


def crash_log(input_str=""):
    latest = _latest_crash()
    if not latest:
        return "✓ No crash logs found."
    try:
        data = _load_crash(latest)
    except Exception as e:
        return f"✗ Could not read crash log: {e}"
    lines = [
        f"=== Crash Report — {data.get('timestamp','?')} ===",
        f"Exception : {data.get('exception_type','?')}",
        f"Message   : {data.get('message','')}",
        "",
        "--- Traceback ---",
        data.get("traceback", "No traceback recorded."),
    ]
    actions = data.get("last_actions", [])
    if actions:
        lines += ["--- Last Actions ---"] + actions
    return "\n".join(lines)


def crash_clear(input_str=""):
    _ensure_crash_dir()
    files = list(CRASH_DIR.glob("crash_*.json"))
    if not files:
        return "✓ No crash logs to clear."
    count = 0
    for f in files:
        try:
            f.unlink()
            count += 1
        except Exception:
            pass
    return f"✓ Cleared {count} crash log(s)."


TOOLS = {
    "crash_status": crash_status,
    "crash_log":    crash_log,
    "crash_clear":  crash_clear,
}

def get_tools(): return TOOLS
