# ============================================================
# Ethica v0.1 — main_window.py
# Primary Application Window
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
from tkinter import ttk
from ui.chat_window import ChatWindow
from ui.ops_popup import OpsPopup
from ui.input_bar import InputBar
from ui.sidebar import Sidebar
from core.ollama_connector import OllamaConnector
from core.llama_connector import LlamaConnector, KNOWN_MODELS
from core.chat_engine import ChatEngine
from ui.canvas_window import CanvasWindow
from ui.dashboard_window import DashboardWindow
from ui.scroll_drop import ScrollDrop
import subprocess
import threading
from pathlib import Path

# ── Ethica Voice ──────────────────────────────────────────────
_TTS_SCRIPT = Path(__file__).parent.parent / "modules" / "gage" / "ethica_tts.py"
_TTS_PYTHON  = Path(__file__).parent.parent / "modules" / "gage" / "gage_env" / "bin" / "python3"
_tts_enabled = True

def _speak(text):
    """Non-blocking TTS — runs in daemon thread via gage_env."""
    if not _tts_enabled:
        return
    if not _TTS_SCRIPT.exists() or not _TTS_PYTHON.exists():
        return
    def _run():
        try:
            subprocess.run(
                [str(_TTS_PYTHON), str(_TTS_SCRIPT), text],
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


class MainWindow:
    """
    Ethica Main Window.
    Orchestrates all UI components.
    Layout:
        ┌─────────────────────────────────────┐
        │  Header (title + status)            │
        ├──────────┬──────────────────────────┤
        │ Sidebar  │  Chat Window             │
        │ (model,  │  (messages)              │
        │  theme)  │                          │
        │          ├──────────────────────────┤
        │          │  Input Bar               │
        └──────────┴──────────────────────────┘
    """

    def __init__(self, root, theme, config):
        self.root = root
        self.theme = theme
        self.config = config

        # ── Backend ───────────────────────────────────────────
        # Try LlamaConnector first (local GGUFs — faster, sovereign)
        # Fall back to Ollama if no GGUFs found
        saved_model = config.get("model", "mistral")
        self._backend = "ollama"

        if saved_model in KNOWN_MODELS:
            connector = LlamaConnector(model_name=saved_model)
            ok, _ = connector.check_connection()
            if ok:
                self._backend = "llama"
        if self._backend == "ollama":
            connector = OllamaConnector(
                host=config.get("ollama_host", "http://localhost:11434"),
                model=saved_model
            )

        self.connector = connector
        self.engine = ChatEngine(self.connector, config)
        self.engine.set_ops_callback(self._route_to_ops, self.root)

        # ── Canvas ────────────────────────────────────────────
        self._ops = None  # OpsPopup — lazy init
        def _canvas_notify(msg):
            self.root.after(0, lambda: self.chat_window.add_message(
                f"⟁ Canvas: {msg}", sender="system"
            ))
        self.canvas = CanvasWindow(
            self.root,
            self.theme,
            self.config,
            on_content_change=self._on_canvas_change,
            connector=self.connector,
            modules=self.engine.modules,
            notify_fn=_canvas_notify
        )
        # Give engine a reference so Ethica can push to canvas
        self.engine.set_canvas(self.canvas)

        # ── Dashboard ─────────────────────────────────────────
        self.dashboard = DashboardWindow(
            self.root,
            self.theme,
            self.config,
            app=self
        )

        # ── Build UI ──────────────────────────────────────────
        self._build_layout()
        self._build_header()
        self._build_body()
        self._register_theme_listeners()

        # ── Greet ─────────────────────────────────────────────
        self._greet()

    # ── Layout ────────────────────────────────────────────────

    def _build_layout(self):
        """Set up main frame structure."""
        c = self.theme.colors

        # Wire close event — trigger reflection on exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Outer container
        self.frame = tk.Frame(
            self.root,
            bg=c["bg_primary"]
        )
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Header frame
        self.header_frame = tk.Frame(
            self.frame,
            bg=c["bg_secondary"],
            height=52
        )
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.header_frame.pack_propagate(False)

        # Body frame (sidebar + chat)
        self.body_frame = tk.Frame(
            self.frame,
            bg=c["bg_primary"]
        )
        self.body_frame.pack(fill=tk.BOTH, expand=True)

    def _build_header(self):
        """Build top header bar."""
        c = self.theme.colors
        f = self.theme.font

        # Left — Ethica title
        title = tk.Label(
            self.header_frame,
            text="✦ Ethica",
            bg=c["bg_secondary"],
            fg=c["accent_bright"],
            font=f("title"),
            padx=16
        )
        title.pack(side=tk.LEFT, pady=10)

        # Right — status indicator
        self.status_dot = tk.Label(
            self.header_frame,
            text="●",
            bg=c["bg_secondary"],
            fg=c["status_offline"],
            font=f("small"),
            padx=4
        )
        # Right — Ollama model timer
        self.model_timer = tk.Label(
            self.header_frame,
            text="",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            padx=12
        )
        self.model_timer.pack(side=tk.RIGHT, pady=10)
        self._model_timer_after = None
        self.status_dot.pack(side=tk.RIGHT, pady=10, padx=4)

        self.status_label = tk.Label(
            self.header_frame,
            text="Connecting...",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("status"),
            padx=4
        )
        self.status_label.pack(side=tk.RIGHT, pady=10)

        # Centre — last tool activity marker
        self.tool_marker = tk.Label(
            self.header_frame,
            text="",
            bg=c["bg_secondary"],
            fg=c.get("accent", "#9b59b6"),
            font=f("small"),
            padx=12
        )
        self.tool_marker.pack(side=tk.LEFT, pady=10)

        # Centre-right — live health bar (CPU / RAM)
        self.health_bar = tk.Label(
            self.header_frame,
            text="",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            padx=12
        )
        self.health_bar.pack(side=tk.LEFT, pady=10)
        self._tool_marker_after = None
        self._health_after = None

        # Separator line under header
        sep = tk.Frame(
            self.frame,
            bg=c["accent_soft"],
            height=1
        )
        sep.pack(fill=tk.X)

    def _build_body(self):
        """Build sidebar + chat area."""
        c = self.theme.colors

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = Sidebar(
            self.body_frame,
            self.theme,
            self.config,
            on_theme_change=self._on_theme_change,
            on_model_change=self._on_model_change,
            on_new_conversation=self._on_new_conversation,
            on_save_toggle=self._on_save_toggle,
            on_open_file=self._on_memory_file_open,
            on_name_save=self._on_name_save
        )
        self.sidebar.on_tool_insert = self._on_tool_insert
        self._save_chat_enabled = False
        self.sidebar.frame.pack(side=tk.LEFT, fill=tk.Y)

        # Vertical separator
        vsep = tk.Frame(
            self.body_frame,
            bg=c["border"],
            width=1
        )
        vsep.pack(side=tk.LEFT, fill=tk.Y)

        # ── Chat area (chat window + input bar) ───────────────
        chat_area = tk.Frame(
            self.body_frame,
            bg=c["bg_primary"]
        )
        chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat display
        self.chat_window = ChatWindow(
            chat_area,
            self.theme,
            self.config
        )
        self.chat_window.frame.pack(fill=tk.BOTH, expand=True)

        # Horizontal separator
        hsep = tk.Frame(
            chat_area,
            bg=c["border"],
            height=1
        )
        hsep.pack(fill=tk.X)

        # Canvas toggle button
        canvas_btn = tk.Button(
            chat_area,
            text="✦ Open Canvas",
            bg=self.theme.get("button_bg"),
            fg=self.theme.get("button_text"),
            font=self.theme.font("small"),
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.canvas.toggle
        )
        canvas_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=12, pady=(0, 4))

        # Scroll Drop zone — above input bar
        self.scroll_drop = ScrollDrop(
            chat_area,
            self.theme,
            self.config,
            on_file_drop=self._on_file_drop
        )
        self.scroll_drop.frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Input bar
        self.input_bar = InputBar(
            chat_area,
            self.theme,
            self.config,
            on_send=self._on_send
        )
        self.input_bar.frame.pack(fill=tk.X, side=tk.BOTTOM)

        # ── Check Ollama connection ───────────────────────────
        self.root.after(500, self._check_connection)
        self.root.after(600, self._start_health_bar)
        self.root.after(1200, self._update_model_timer)
        self.root.after(1500, self._start_mnemis)

    # ── Event Handlers ────────────────────────────────────────

    def _on_file_drop(self, filepath):
        """Called when a file is dropped onto scroll drop zone."""
        import os
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filepath)[1].lower()

        # Code files — WormBot scan → Ops
        CODE_EXTS = {'.py', '.js', '.rs', '.sh', '.css', '.html'}
        if ext in CODE_EXTS:
            self.chat_window.add_message(
                f"⟁ Scanning: {filename}",
                sender="system"
            )
            self.canvas.open()
            self.input_bar.set_enabled(False)

            def on_response(text):
                import os
                self.root.after(0, lambda: self._route_to_ops("WormBot", text, os.path.basename(filepath)))

            def on_error(err):
                self.root.after(0, lambda: self.chat_window.add_message(f"⚠ {err}", sender="system"))

            def on_done():
                self.root.after(0, lambda: self.input_bar.set_enabled(True))

            self.engine.send(filepath, on_response, on_error, on_done)
        elif ext == '.pdf':
            # PDF — extract text + render pages as two canvas tabs
            self.canvas.open()
            self.root.after(100, lambda: self.canvas._drop_as_pdf(filepath))
        elif ext in ('.png', '.jpg', '.jpeg'):
            # Image — render in canvas Document tab
            self.canvas.open()
            self.root.after(100, lambda: self.canvas._drop_as_image(filepath))
        else:
            # Document files — route to canvas as Document tab
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read()
            except Exception as e:
                self.chat_window.add_message(f"⚠ Could not read {filename}: {e}", sender="system")
                return
            self.canvas.open()
            self.root.after(100, lambda: self.canvas._drop_as_document(file_content, filename))

    def _start_mnemis(self):
        """Start Mnemis watcher and run initial index at boot."""
        try:
            if self.engine.modules.has_tool("mnemis_status"):
                def _notify(msg):
                    self.root.after(0, lambda: self.chat_window.add_message(
                        f"⟁ Mnemis: {msg}", sender="system"
                    ))
                import importlib
                mod = None
                for m in self.engine.modules._modules.values():
                    if m.name == "Mnemis" and m.impl is not None:
                        mod = m.impl
                        break
                if mod and hasattr(mod, 'init'):
                    mod.init(notify_fn=_notify)
        except Exception as e:
            print(f"[Mnemis] boot error: {e}")

    def _start_health_bar(self):
        """Start the live CPU/RAM health bar — updates every 5s."""
        try:
            import psutil
            self._psutil = psutil
            self._update_health()
        except ImportError:
            pass

    def _update_health(self):
        """Poll CPU and RAM, update header label."""
        try:
            cpu = self._psutil.cpu_percent(interval=None)
            ram = self._psutil.virtual_memory()
            self.health_bar.config(
                text=f"CPU {cpu:.0f}%  RAM {ram.percent:.0f}%"
            )
            # Colour hint — green/yellow/red
            if cpu > 80 or ram.percent > 85:
                self.health_bar.config(fg="#e74c3c")
            elif cpu > 50 or ram.percent > 65:
                self.health_bar.config(fg="#f39c12")
            else:
                self.health_bar.config(fg=self.theme.colors["text_muted"])
        except Exception:
            pass
        self._health_after = self.root.after(5000, self._update_health)

    def _update_model_timer(self):
        """Poll ollama ps — show loaded model and countdown in header."""
        try:
            import subprocess, re
            result = subprocess.run(
                ["ollama", "ps"],
                capture_output=True, text=True, timeout=3
            )
            lines = result.stdout.strip().splitlines()
            # Find first model line (skip header)
            model_line = next((l for l in lines[1:] if l.strip()), None)
            if model_line:
                parts = model_line.split()
                model_name = parts[0].split(":")[0]  # strip :latest
                # Find UNTIL — last two words e.g. "3 minutes from now"
                until_match = re.search(r'(\d+)\s+(second|minute|hour)s?\s+from now', model_line)
                if until_match:
                    val = int(until_match.group(1))
                    unit = until_match.group(2)
                    if unit == "second":
                        countdown = f"{val}s"
                        fg = "#e74c3c"
                    elif unit == "minute":
                        countdown = f"{val}m"
                        fg = "#f39c12" if val <= 2 else self.theme.colors["text_muted"]
                    else:
                        countdown = f"{val}h"
                        fg = self.theme.colors["text_muted"]
                    self.model_timer.config(
                        text=f"🧠 {model_name} · {countdown}",
                        fg=fg
                    )
                else:
                    self.model_timer.config(text=f"🧠 {model_name}", fg=self.theme.colors["text_muted"])
            else:
                self.model_timer.config(text="")
        except Exception:
            pass
        self._model_timer_after = self.root.after(10000, self._update_model_timer)

    def _set_tool_marker(self, text, duration_ms=4000):
        """Show brief tool activity in header — auto-clears."""
        if self._tool_marker_after:
            self.root.after_cancel(self._tool_marker_after)
            self._tool_marker_after = None
        self._health_after = None
        self.tool_marker.config(text=text)
        self._tool_marker_after = self.root.after(
            duration_ms,
            lambda: self.tool_marker.config(text="")
        )

    def _on_memory_file_open(self, filepath):
        """Open a memory file in the canvas tab."""
        self.canvas.open()
        self.canvas.open_file(filepath)

    def _on_tool_insert(self, syntax):
        """Insert tool syntax into chat input from Tool Lister."""
        if hasattr(self, 'input_bar') and self.input_bar:
            self.input_bar.insert_text(syntax)

    def _on_name_save(self):
        """Called when user saves new names — reset engine so new identity takes effect."""
        self.engine.reset()
        ethica_name = self.config.get("ethica_name", "Ethica")
        user_name = self.config.get("user_name", "Friend")
        self.chat_window.add_message(
            f"Names updated. I'm {ethica_name} — good to meet you, {user_name}.",
            sender="ethica",
            name=ethica_name
        )

    def _on_save_toggle(self, enabled):
        """Called when chat save toggle changes."""
        self._save_chat_enabled = enabled
        status = "ON" if enabled else "OFF"
        self.chat_window.add_message(
            f"⟁ Chat save {status}",
            sender="system"
        )

    def _save_chat_to_disk(self):
        """Save current chat log to memory/chat/ as timestamped file."""
        import os
        from datetime import datetime
        from pathlib import Path
        history = self.engine.history if hasattr(self.engine, 'history') else []
        if not history:
            return
        chat_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "memory" / "chat"
        chat_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = chat_dir / f"chat_{ts}.txt"
        import re as _re
        lines = []
        for msg in history:
            role = msg.get("role", "?").upper()
            text = msg.get("content", "")
            # Strip <think> blocks
            text = _re.sub(r'<think>.*?</think>', '', text, flags=_re.DOTALL).strip()
            if text:
                lines.append(f"[{role}]: {text}")
        filepath.write_text("\n\n".join(lines), encoding="utf-8")
        print(f"[ChatSave] Saved to {filepath}")

    def _route_to_ops(self, tool_name, result, label=None):
        """Route tool result to Ops popup. Show brief marker in chat.
        Runs result through canvas push handler first — code goes to debug tab."""
        # Dashboard sentinel — open dashboard instead of routing to ops
        if result and result.strip() == "__OPEN_DASHBOARD__":
            self.dashboard.open()
            self.chat_window.add_message("⟁ Dashboard open.", sender="system")
            self._set_tool_marker("⟁ Dashboard")
            return
        # Lazy init ops popup
        if self._ops is None:
            self._ops = OpsPopup(self.root, self.theme, self.config)
            self._ops.set_canvas(self.canvas)
            # Re-register drop zone — new Toplevel breaks tkinterdnd2 registration
            self.root.after(100, self.scroll_drop.reregister_drop)
        # Always run through canvas push — strips DEBUG markers, pushes to canvas if open
        try:
            processed = self.engine._handle_canvas_push(result, tool_result=True)
        except Exception as e:
            print(f"[Ops] canvas push error: {e}")
            processed = result
        # Push processed result to ops
        self._ops.push(tool_name, processed)
        # Drain integrity warning if any
        try:
            import json, os
            _iw_path = os.path.expanduser("~/Ethica/status/integrity_warning.json")
            if os.path.exists(_iw_path):
                with open(_iw_path) as _f:
                    _iw = json.load(_f)
                os.remove(_iw_path)
                self._ops.push("IntegrityShield", 
                    f"⚠ Architecture tampering detected!\n"
                    f"{_iw.get('warning', '')}\n\n"
                    f"Ethica learns from every session — your tool patterns, preferences and "
                    f"context are built over time. Tampering with core files risks losing "
                    f"everything she has learned about you.\n"
                    f"Run 'guard verify' for details or 'guard heal all' to restore."
                )
        except Exception:
            pass
        # Brief marker in chat
        self.chat_window.add_message(
            f"⟁ {tool_name} → Ops",
            sender="system"
        )
        # Header status marker — auto-clears after 4s
        self._set_tool_marker(f"⟁ {tool_name} → Ops")

    def _on_send(self, message):
        """Called when user sends a message."""
        if not message.strip():
            return

        # Display user message
        self.chat_window.add_message(
            message,
            sender="user",
            name=self.config.get("user_name", "You")
        )

        # Detect tool triggers — route to ops instead of chat bubble
        import re as _re
        _is_tool = self.engine.is_tool_trigger(message)

        if _is_tool:
            # Tool path — no streaming bubble, result goes to ops
            self.status_dot.config(fg=self.theme.get("status_thinking"))
            self.status_label.config(text="Running tool...")
            self.input_bar.set_enabled(False)
            _tool_name = message.strip().split()[0:2]
            _tool_label = " ".join(_tool_name).title()
            self.engine.send(
                message,
                on_response=lambda r: self.root.after(0, self._route_to_ops, _tool_label, r),
                on_error=lambda e: self.root.after(0, self._on_error, e),
                on_done=lambda: self.root.after(0, self._on_done),
                on_token=None
            )
            return

        # Start streaming bubble — Ethica thinks out loud
        ethica_name = self.config.get("ethica_name", "Ethica")
        append_token, finalize_bubble = self.chat_window.start_stream_bubble(
            name=ethica_name
        )

        # Store finalize so _on_response can close the bubble
        self._finalize_bubble = finalize_bubble

        # Update status
        self.status_dot.config(fg=self.theme.get("status_thinking"))
        self.status_label.config(text="Thinking...")
        self.input_bar.set_enabled(False)

        # Send to engine — tokens stream to bubble in real time
        # Batch tokens every 50ms to reduce UI event queue pressure
        self._token_buffer = []
        self._stream_active = True
        self._suppress_stream = False
        self._suppressed_buffer = []

        def flush_tokens():
            """Flush buffered tokens to bubble in one UI update."""
            if self._token_buffer and not self._suppress_stream:
                combined = "".join(self._token_buffer)
                self._token_buffer.clear()
                append_token(combined)
            elif self._suppress_stream:
                self._token_buffer.clear()
            if self._stream_active:
                self.root.after(50, flush_tokens)

        def buffer_token(token):
            # Token-level canvas/debug suppression
            if self._suppress_stream:
                self._suppressed_buffer.append(token)
                return
            # Detect opening markers — enter suppression mode
            _so_far = "".join(self._token_buffer) + token
            _triggers = ("[CANVAS:", "[DEBUG:", "```")
            if any(t in _so_far for t in _triggers):
                _cut = len(_so_far)
                for t in _triggers:
                    idx = _so_far.find(t)
                    if idx != -1 and idx < _cut:
                        _cut = idx
                intent = _so_far[:_cut]
                self._token_buffer.clear()
                if intent.strip():
                    self._token_buffer.append(intent)
                self._suppress_stream = True
                self._suppressed_buffer.append(_so_far[_cut:])
                return
            self._token_buffer.append(token)

        # Start flush loop
        self.root.after(50, flush_tokens)

        self.engine.send(
            message,
            on_response=lambda r: self.root.after(0, self._on_response, r),
            on_error=lambda e: self.root.after(0, self._on_error, e),
            on_done=lambda: self.root.after(0, self._on_done),
            on_token=buffer_token
        )

    def _on_response(self, response):
        """Called on main thread when Ethica's full response is ready."""
        # Sentinel intercept — Ethica invoking her own tools
        if response and "__OPEN_DASHBOARD__" in response:
            if hasattr(self, '_finalize_bubble') and self._finalize_bubble:
                self._finalize_bubble("")
                self._finalize_bubble = None
            self.dashboard.open()
            self.chat_window.add_message("⟁ Dashboard open.", sender="system")
            self._restore_ready()
            return
        # Finalize the streaming bubble — swap live Text for static Label
        # Suppress canvas/debug push confirmations — they belong on canvas, not chat
        _canvas_sentinels = (
            "→ Sent to canvas",
            "→ Code sent to debug tab",
            "→ Tasks added to canvas",
            "→ Annotation added to sketch",
        )
        if response and any(response.strip().endswith(s) or response.strip() == s
                            for s in _canvas_sentinels):
            # Strip the sentinel — show only any preceding conversational text
            for s in _canvas_sentinels:
                if response.strip() == s:
                    # Pure sentinel — suppress entirely
                    self._finalize_bubble = None
                    self._restore_ready()
                    return
                if response.strip().endswith(s):
                    response = response[:response.rfind(s)].strip()
                    break

        # Strip canvas/code content from bubble — show intent text only
        # Note: ``` is intentionally excluded here — handled by fallback extractor below
        if response:
            _strip_markers = ("[CANVAS:", "[DEBUG:")
            for _m in _strip_markers:
                _mi = response.find(_m)
                if _mi != -1:
                    response = response[:_mi].strip()
                    break

        # Fallback — catch fenced code blocks the model wrote directly in chat
        # Extract them, push to canvas, keep only intent text in bubble
        if response and '```' in response:
            import re as _re
            _fences = list(_re.finditer(r'```(\w*)\s*\n([\s\S]*?)```', response))
            if _fences:
                _intent = response[:_fences[0].start()].strip()
                for _fence in _fences:
                    _lang = _fence.group(1).strip() or "python"
                    _code = _fence.group(2).strip()
                    if _code and hasattr(self, '_canvas') and self._canvas:
                        self._canvas.push_debug_from_ethica(_code, tab_name="Debug", lang=_lang)
                response = _intent or "→ Sent to canvas."

        if hasattr(self, '_finalize_bubble') and self._finalize_bubble:
            self._finalize_bubble(response)
            self._finalize_bubble = None
        _speak(response)
        self._restore_ready()
        # Auto-save if enabled
        if getattr(self, '_save_chat_enabled', False):
            self._save_chat_to_disk()

    def _on_error(self, error):
        """Called on main thread when something goes wrong."""
        # Finalize bubble with error message if it exists
        if hasattr(self, '_finalize_bubble') and self._finalize_bubble:
            self._finalize_bubble(f"⚠ {error}")
            self._finalize_bubble = None
        else:
            self.chat_window.add_message(f"⚠ {error}", sender="system")
        self.status_dot.config(fg=self.theme.get("status_offline"))
        self.status_label.config(text="Error — try again")

    def _on_done(self):
        """
        Always called after every send — success or failure.
        Guaranteed re-enable of input bar.
        """
        self._stream_active = False
        self._suppress_stream = False
        self._suppressed_buffer = []
        # Flush any remaining buffered tokens
        if hasattr(self, '_token_buffer') and self._token_buffer:
            combined = "".join(self._token_buffer)
            self._token_buffer.clear()
        self.input_bar.set_enabled(True)
        self.input_bar.focus()
        self.status_label.config(text="")

    def _restore_ready(self):
        """Restore status to ready state."""
        self.status_dot.config(fg=self.theme.get("status_online"))
        self.status_label.config(
            text=f"Ready  ·  {self.config.get('model', 'local')}"
        )

    def _on_theme_change(self, theme_name):
        """Called when user selects a new theme."""
        if self.theme.switch(theme_name):
            self.config.set("theme", theme_name)
            self.config.save()
            self._refresh_theme()

    def _on_model_change(self, model_name):
        """Called when user selects a new model — switch backend if needed."""
        # Skip section headers
        if model_name.startswith("──"):
            return

        # Merge sidebar scanned paths into KNOWN_MODELS at runtime
        if hasattr(self.sidebar, '_gguf_model_paths'):
            KNOWN_MODELS.update(self.sidebar._gguf_model_paths)

        if model_name in KNOWN_MODELS:
            # Switch to LlamaConnector
            if not isinstance(self.connector, LlamaConnector):
                self.connector = LlamaConnector(model_name)
                self.engine.ollama = self.connector
                self._backend = "llama"
            else:
                self.connector.set_model(model_name)
        else:
            # Switch to Ollama
            if not isinstance(self.connector, OllamaConnector):
                self.connector = OllamaConnector(
                    host=self.config.get("ollama_host", "http://localhost:11434"),
                    model=model_name
                )
                self.engine.ollama = self.connector
                self._backend = "ollama"
            else:
                self.connector.set_model(model_name)

        self.config.set("model", model_name)
        self.config.save()

        # Update status
        backend_label = "local" if self._backend == "llama" else "ollama"
        self.root.after(0, lambda: self.status_label.config(
            text=f"Ready  ·  {model_name}  ({backend_label})"
        ))

    def _on_new_conversation(self):
        """Clear chat and reset engine for a fresh conversation."""
        self.engine.reset()
        self.chat_window.clear()
        ethica_name = self.config.get("ethica_name", "Ethica")
        user_name = self.config.get("user_name", "Friend")
        _greeting = f"Hello {user_name}. I'm {ethica_name}.\n\nI'm here when you're ready. What are we thinking about today?"
        self.chat_window.add_message(
            _greeting,
            sender="ethica",
            name=ethica_name
        )
        _speak(_greeting)

    def _on_close(self):
        """Called when app window closes — trigger reflection then exit."""
        try:
            # Trigger background reflection
            self.engine.reflection.reflect_after_session(
                self.engine._exchange_count
            )
            # Give reflection thread a moment to start
            import time
            time.sleep(0.3)
        except Exception:
            pass
        try:
            self.engine.memory.close_session()
        except Exception:
            pass
        self.root.destroy()

    def _refresh_theme(self):
        """Live theme refresh — no restart needed."""
        # ThemeEngine.switch() already notified all listeners
        # This is kept for any additional window-level chrome
        self.root.config(bg=self.theme.get("bg_primary"))

    # ── Connection Check ──────────────────────────────────────

    def _check_connection(self):
        """Check if backend is reachable — thread-safe via queue."""
        import threading
        import queue as _queue
        ui_queue = _queue.Queue()

        def check():
            ok, info = self.connector.check_connection()
            model_name = self.config.get("model", "mistral")
            backend = "local" if self._backend == "llama" else "ollama"
            ui_queue.put(("ok" if ok else "fail", model_name, backend, info))

        def drain():
            try:
                status, model_name, backend, info = ui_queue.get_nowait()
                if status == "ok":
                    self.status_dot.config(fg=self.theme.get("status_online"))
                    self.status_label.config(
                        text=f"Ready  \u00b7  {model_name}  ({backend})"
                    )
                else:
                    self.status_dot.config(fg=self.theme.get("status_offline"))
                    if self._backend == "llama":
                        self.status_label.config(text="Model not found \u2014 check path")
                        self.chat_window.add_message(
                            f"\u26a0 Could not load model.\n{info}",
                            sender="system"
                        )
                    else:
                        self.status_label.config(text="Ollama not found \u2014 is it running?")
                        self.chat_window.add_message(
                            "Start Ollama and select a model in the sidebar to begin.",
                            sender="system"
                        )
            except _queue.Empty:
                self.root.after(100, drain)

        threading.Thread(target=check, daemon=True).start()
        self.root.after(100, drain)


    # ── Greeting ──────────────────────────────────────────────

    def _greet(self):
        """Ethica's first words — warm, not corporate."""
        name = self.config.get("user_name", "Friend")
        ethica_name = self.config.get("ethica_name", "Ethica")

        # ── TrinityGuard startup integrity check ──────────────
        try:
            from modules.ethica_guard.ethica_guard import startup_check
            warning = startup_check()
            if warning:
                self.chat_window.add_message(
                    warning,
                    sender="ethica",
                    name=ethica_name
                )
        except Exception:
            pass

        greeting = (
            f"Hello {name}. I'm {ethica_name}.\n\n"
            f"I'm here when you're ready. What shall we build today?"
        )
        self.chat_window.add_message(
            greeting,
            sender="ethica",
            name=ethica_name
        )
        _speak(greeting)

    # ── Live Theme Refresh ────────────────────────────────────

    def apply_theme(self):
        """
        Repaint main window chrome with current theme.
        Called automatically by ThemeEngine on theme switch.
        """
        c = self.theme.colors

        self.root.config(bg=c["bg_primary"])
        self.frame.config(bg=c["bg_primary"])
        self.header_frame.config(bg=c["bg_secondary"])
        self.body_frame.config(bg=c["bg_primary"])

        # Header labels
        for widget in self.header_frame.winfo_children():
            try:
                widget.config(bg=c["bg_secondary"])
            except Exception:
                pass

    def _on_canvas_change(self, context):
        """Called when canvas content changes — updates Ethica's context."""
        self.engine.update_canvas_context(context)

    def _register_theme_listeners(self):
        """
        Register all components with ThemeEngine.
        Order matters — main window first, then children.
        """
        self.theme.register(self.apply_theme)
        self.theme.register(self.sidebar.apply_theme)
        self.theme.register(self.chat_window.apply_theme)
        self.theme.register(self.input_bar.apply_theme)
        self.theme.register(self.scroll_drop.apply_theme)
        self.theme.register(self.canvas.apply_theme)
