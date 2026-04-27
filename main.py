# ============================================================
# Ethica v0.1 — main.py
# Application Entry Point
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
try:
    from tkinterdnd2 import TkinterDnD
    _DND = True
except ImportError:
    _DND = False
import sys
import os
import logging

# ── Logging Setup ─────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_LOG_DIR, 'ethica.log')),
        logging.StreamHandler(),
    ]
)

# ── Path Setup (portable — no absolute paths) ─────────────────
# Ensures all imports work regardless of where Ethica is installed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Imports ───────────────────────────────────────────────────
from ui.theme import theme
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from modules.crash_reporter.crash_reporter_tool import install_excepthook, check_crash_log
from modules.ethica_guard.ethica_guard import startup_check


# ── Boot Sequence ─────────────────────────────────────────────

def boot():
    """
    Ethica boot sequence.
    1. Load user config (theme preference, model selection, etc.)
    2. Apply saved theme
    3. Launch main window
    """

    # Load user config — creates default if none exists
    config = ConfigManager()

    # Apply saved theme preference
    saved_theme = config.get("theme", "purple")
    theme.switch(saved_theme)

    # Init Tkinter root
    root = TkinterDnD.Tk() if _DND else tk.Tk()
    root.title("Ethica")
    root.geometry("900x680")
    root.minsize(700, 500)

    # Apply window background immediately — no white flash on load
    root.configure(bg=theme.get("bg_primary"))

    # Center window on screen
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = 900
    win_h = 680
    x = (screen_w // 2) - (win_w // 2)
    y = (screen_h // 2) - (win_h // 2)
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # Remove default title bar border (clean look)
    # root.overrideredirect(True)  # Uncomment for frameless — Phase 2

    # Launch main window — passes root, theme, config
    # Launch persistent voice server (XTTS — loads model once)
    import subprocess as _sp, threading as _th, pathlib as _pl
    _VOICE_SERVER = _pl.Path(BASE_DIR) / "modules" / "ethica_voice" / "ethica_voice_server.py"
    _VOICE_PYTHON = _pl.Path(BASE_DIR) / "modules" / "gage" / "gage_env" / "bin" / "python3"
    _voice_setting = config.get('voice_enabled', 'auto')
    if _voice_setting == 'auto':
        try:
            import torch as _torch
            _voice_on = _torch.cuda.is_available()
            print(f'[Ethica] Voice auto-detect: {"GPU found — voice ON" if _voice_on else "CPU only — voice OFF"}')
        except Exception:
            _voice_on = False
            print('[Ethica] Voice auto-detect: torch unavailable — voice OFF')
    elif _voice_setting is True or str(_voice_setting).lower() == 'true':
        _voice_on = True
        print('[Ethica] Voice: forced ON (config)')
    else:
        _voice_on = False
        print('[Ethica] Voice: forced OFF (config)')
    if _voice_on and _VOICE_SERVER.exists() and _VOICE_PYTHON.exists():
        _vs_proc = _sp.Popen(
            [str(_VOICE_PYTHON), str(_VOICE_SERVER)],
            stdout=_sp.PIPE, stderr=_sp.STDOUT, text=True
        )
        def _watch_voice_server(proc):
            for line in proc.stdout:
                print(line, end="", flush=True)
        _th.Thread(target=_watch_voice_server, args=(_vs_proc,), daemon=True).start()
        print("[Ethica] Voice server launching...", flush=True)

    app = MainWindow(root, theme, config)

    # ── HTTP Trigger (VIVARIUM bridge — port 5006) ────────────
    def _start_http_trigger(root, app):
        import http.server, json, threading

        class _TriggerHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # silence access log

            def do_GET(self):
                if self.path == '/ping':
                    body = json.dumps({"status": "alive", "body": "Ethica"}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == '/trigger':
                    try:
                        length = int(self.headers.get('Content-Length', 0))
                        raw = self.rfile.read(length)
                        data = json.loads(raw)
                        message = data.get('message', '').strip()
                        if message:
                            root.after(0, app._on_send, message)
                            body = json.dumps({"status": "ok", "message": message}).encode()
                            self.send_response(200)
                        else:
                            body = json.dumps({"status": "error", "reason": "empty message"}).encode()
                            self.send_response(400)
                    except Exception as exc:
                        body = json.dumps({"status": "error", "reason": str(exc)}).encode()
                        self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

        server = http.server.HTTPServer(('127.0.0.1', 5006), _TriggerHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print('[Ethica] HTTP trigger listening on 127.0.0.1:5006', flush=True)

    _start_http_trigger(root, app)

    # ── VIVARIUM boot read — shared_state awareness
    def _read_vivarium_state():
        import json, os
        state_path = os.path.expanduser("~/.trinity/shared_state.json")
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
            mini = state.get("minitrini", {})
            if mini.get("port"):
                print(f"[Ethica] VIVARIUM — MiniTrini LIVE on port {mini['port']} | agent: {mini.get('agent','?')} | last: {mini.get('timestamp','?')}", flush=True)
            else:
                print("[Ethica] VIVARIUM — MiniTrini state: not found", flush=True)
        except Exception:
            print("[Ethica] VIVARIUM — shared_state unreadable or missing", flush=True)
    import threading as _vt
    _vt.Thread(target=_read_vivarium_state, daemon=True).start()

    # ─────────────────────────────────────────────────────────

    # Install global crash handler — before mainloop
    install_excepthook()

    # Check for crash log from previous session
    check_crash_log(root)
    # Integrity check — warn if architecture tampered
    _integrity_warning = startup_check()
    if _integrity_warning:
        import tkinter.messagebox as mb
        mb.showwarning(
            '⚠ Ethica Integrity Warning',
            f'{_integrity_warning}\n\n'
            'If you did not make these changes, Ethica\'s architecture may have been tampered with.\n\n'
            'Continuing may result in loss of all learned memory, tool usage history, and retained context.\n'
            'A fresh install may be required to restore integrity.\n\n'
            'Proceeding anyway.'
        )

    # Handle clean close
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, config, app))

    # Start event loop
    root.mainloop()


def on_close(root, config, app=None):
    """
    Clean shutdown.
    Save any unsaved config before exit.
    """
    config.save()
    if app is not None:
        try:
            app._on_close()
            return  # _on_close calls root.destroy() itself
        except Exception:
            pass
    root.destroy()


# ── Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    boot()
