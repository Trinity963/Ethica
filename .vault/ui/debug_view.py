# ============================================================
# Ethica v0.1 — debug_view.py
# Debug Canvas Tab — Split View with Ethica Commentary
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Code on the left. Output on the right.
# Ethica always comments — brief on success, focused on failure.
# She sees what you see. She thinks about it.
#
# Languages: Python (first), expandable
# Persists code across sessions as JSON in CanvasTab.content
# ============================================================

import logging
import re
import tkinter as tk
from tkinter import ttk
import json
import subprocess
import sys
import os
import threading
import tempfile
from datetime import datetime
from core.autonomous_debugger import AutonomousDebugger


# ── Language Definitions ──────────────────────────────────────

LANGUAGES = {
    "Python": {
        "ext":        ".py",
        "runner":     sys.executable,
        "comment":    "#",
        "placeholder": "# Write your code here\nprint('hello world')\n"
    },
    "Bash": {
        "ext":        ".sh",
        "runner":     "/bin/bash",
        "comment":    "#",
        "placeholder": "#!/bin/bash\necho 'hello world'\n"
    },
    "JavaScript": {
        "ext":        ".js",
        "runner":     "node",
        "comment":    "//",
        "placeholder": "// JavaScript\nconsole.log('hello world');\n"
    },
    "CSS": {
        "ext":        ".css",
        "runner":     None,
        "comment":    "/*",
        "placeholder": "/* CSS */\nbody {\n    margin: 0;\n}\n"
    },
    "HTML": {
        "ext":        ".html",
        "runner":     None,
        "comment":    "<!--",
        "placeholder": "<!DOCTYPE html>\n<html>\n<body>\n</body>\n</html>\n"
    },
    "JSON": {
        "ext":        ".json",
        "runner":     None,
        "comment":    None,
        "placeholder": "{\n    \"key\": \"value\"\n}\n"
    },
    "Markdown": {
        "ext":        ".md",
        "runner":     None,
        "comment":    None,
        "placeholder": "# Title\n\nContent here.\n"
    },
    "Rust": {
        "ext":        ".rs",
        "runner":     "rustc",
        "comment":    "//",
        "placeholder": "// Rust\nfn main() {\n    println!(\"hello world\");\n}\n"
    },
    "YAML": {
        "ext":        ".yaml",
        "runner":     None,
        "comment":    "#",
        "placeholder": "# YAML\nkey: value\n"
    },
}

DEFAULT_LANG = "Python"


class DebugRun:
    """Result of a single debug execution."""
    def __init__(self, code, stdout, stderr, returncode, duration, timestamp):
        self.code       = code
        self.stdout     = stdout
        self.stderr     = stderr
        self.returncode = returncode
        self.duration   = duration
        self.timestamp  = timestamp
        self.success    = returncode == 0 and not stderr.strip()

    @property
    def has_error(self):
        return bool(self.stderr.strip()) or self.returncode != 0

    def extract_error_summary(self):
        """Pull the most relevant error line from traceback."""
        if not self.stderr:
            return None
        lines = self.stderr.strip().splitlines()
        # Last line is usually the exception type + message
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("File") and not line.startswith("Traceback"):
                return line
        return lines[-1] if lines else None

    def extract_error_line(self):
        """Extract the line number from traceback if available."""
        if not self.stderr:
            return None
        matches = re.findall(r'line (\d+)', self.stderr)
        return int(matches[-1]) if matches else None


class DebugView:
    """
    Split-pane debug surface.
    Left: code editor with line numbers.
    Right: output panel — stdout green, stderr red, Ethica comment purple.
    """

    def __init__(self, parent, theme, connector, config, on_change=None):
        self.parent    = parent
        self.theme     = theme
        self.connector = connector
        self.config    = config
        self.on_change = on_change

        self._lang        = DEFAULT_LANG
        self._running     = False
        self._auto_running = False
        self._run_history = []
        self._frame       = None
        self._editor      = None
        self._output      = None
        self._auto_debugger = AutonomousDebugger(connector, config)

        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._frame = tk.Frame(self.parent, bg=c["bg_primary"])
        self._frame.pack(fill=tk.BOTH, expand=True)

        # ── Toolbar ───────────────────────────────────────────
        toolbar = tk.Frame(self._frame, bg=c["bg_secondary"], pady=4)
        toolbar.pack(fill=tk.X)

        # Run button
        self._run_btn = tk.Button(
            toolbar,
            text="▶  Run",
            bg=c["accent_soft"],
            fg=c["accent_bright"],
            font=f("body_bold"),
            relief=tk.FLAT,
            padx=14,
            pady=3,
            cursor="hand2",
            command=self._run_code
        )
        self._run_btn.pack(side=tk.LEFT, padx=(8, 4))

        # Auto-fix button — Ethica's autonomous debug loop
        self._autofix_btn = tk.Button(
            toolbar,
            text="⟁ Auto-fix",
            bg=c["bg_secondary"],
            fg=c["accent_bright"],
            font=f("body_bold"),
            relief=tk.FLAT,
            padx=14,
            pady=3,
            cursor="hand2",
            command=self._run_autofix
        )
        self._autofix_btn.pack(side=tk.LEFT, padx=(0, 4))

        # Language selector
        tk.Label(
            toolbar,
            text="Lang:",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small")
        ).pack(side=tk.LEFT, padx=(8, 2))

        self._lang_var = tk.StringVar(value=DEFAULT_LANG)
        lang_menu = ttk.Combobox(
            toolbar,
            textvariable=self._lang_var,
            values=list(LANGUAGES.keys()),
            state="readonly",
            width=8,
            font=f("small")
        )
        lang_menu.pack(side=tk.LEFT, padx=(0, 8))
        lang_menu.bind("<<ComboboxSelected>>", self._on_lang_change)

        # Status indicator
        self._status_label = tk.Label(
            toolbar,
            text="Ready",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small")
        )
        self._status_label.pack(side=tk.LEFT, padx=8)

        # Clear output button
        tk.Button(
            toolbar,
            text="Clear output",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._clear_output
        ).pack(side=tk.RIGHT, padx=8)

        # ── Split pane ────────────────────────────────────────
        pane = tk.PanedWindow(
            self._frame,
            orient=tk.HORIZONTAL,
            bg=c["bg_tertiary"],
            sashwidth=4,
            sashrelief=tk.FLAT
        )
        pane.pack(fill=tk.BOTH, expand=True)

        # ── Left: Code editor ─────────────────────────────────
        left = tk.Frame(pane, bg=c["bg_primary"])
        pane.add(left, minsize=200)

        # Column header
        tk.Label(
            left,
            text="  CODE",
            bg=c["bg_tertiary"],
            fg=c["text_muted"],
            font=f("small"),
            anchor=tk.W,
            pady=3
        ).pack(fill=tk.X)

        # Line numbers + editor
        editor_frame = tk.Frame(left, bg=c["bg_primary"])
        editor_frame.pack(fill=tk.BOTH, expand=True)

        self._line_numbers = tk.Text(
            editor_frame,
            width=4,
            bg=c["bg_tertiary"],
            fg=c["text_muted"],
            font=("Courier New", 12),
            state=tk.DISABLED,
            relief=tk.FLAT,
            cursor="arrow",
            padx=4
        )
        self._line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self._line_numbers.tag_config(
            "line_highlight",
            background="#3a3a5a",
            foreground="#ffffff"
        )

        editor_scroll = tk.Scrollbar(editor_frame, orient=tk.VERTICAL)
        editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._editor = tk.Text(
            editor_frame,
            bg=c["bg_primary"],
            fg=c["text_primary"],
            font=("Courier New", 12),
            insertbackground=c["accent_bright"],
            relief=tk.FLAT,
            padx=8,
            pady=4,
            undo=True,
            tabs="4c",
            yscrollcommand=editor_scroll.set,
            wrap=tk.NONE
        )
        self._editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        editor_scroll.config(command=self._sync_scroll)

        # Syntax highlight colors
        self._editor.tag_config("error_line",
            background="#3a0a0a",
            foreground="#ff6b6b"
        )

        # Bind events
        self._editor.bind("<KeyRelease>", self._update_line_numbers)
        self._editor.bind("<MouseWheel>", self._on_mousewheel)
        self._editor.bind("<ButtonPress-1>", self._on_line_click)

        # Insert placeholder
        lang_def = LANGUAGES[self._lang]
        self._editor.insert("1.0", lang_def["placeholder"])
        self._update_line_numbers()

        # Keyboard shortcut — Ctrl+Enter to run
        self._editor.bind("<Control-Return>", lambda e: self._run_code())

        # ── Right: Output panel ───────────────────────────────
        right = tk.Frame(pane, bg=c["bg_primary"])
        pane.add(right, minsize=200)

        tk.Label(
            right,
            text="  OUTPUT",
            bg=c["bg_tertiary"],
            fg=c["text_muted"],
            font=f("small"),
            anchor=tk.W,
            pady=3
        ).pack(fill=tk.X)

        output_scroll = tk.Scrollbar(right, orient=tk.VERTICAL)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._output = tk.Text(
            right,
            bg="#0a0a14",
            fg=c["text_primary"],
            font=("Courier New", 11),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            state=tk.DISABLED,
            wrap=tk.WORD,
            yscrollcommand=output_scroll.set
        )
        self._output.pack(fill=tk.BOTH, expand=True)
        output_scroll.config(command=self._output.yview)

        # Output text tags
        self._output.tag_config("timestamp",
            foreground=c["text_muted"],
            font=("Courier New", 10)
        )
        self._output.tag_config("stdout",
            foreground="#69db7c"   # green
        )
        self._output.tag_config("stderr",
            foreground="#ff6b6b"   # red
        )
        self._output.tag_config("traceback",
            foreground="#ffa94d"   # orange
        )
        self._output.tag_config("success_label",
            foreground="#69db7c",
            font=("Courier New", 10)
        )
        self._output.tag_config("error_label",
            foreground="#ff6b6b",
            font=("Courier New", 10)
        )
        self._output.tag_config("ethica_comment",
            foreground=c["accent_bright"],
            font=("Inter", 11),
            lmargin1=8,
            lmargin2=8
        )
        self._output.tag_config("ethica_label",
            foreground=c["accent_soft"],
            font=("Inter", 10)
        )
        self._output.tag_config("separator",
            foreground=c["bg_tertiary"]
        )

    # ── Run ───────────────────────────────────────────────────

    def _run_code(self):
        try:
            if self._running:
                return
            if not self._run_btn.winfo_exists():
                return

            code = self._editor.get("1.0", tk.END).strip()
            if not code:
                return

            self._running = True
            self._run_btn.config(text="⏳ Running...", state=tk.DISABLED)
            self._status_label.config(text="Running...")

            # Clear error highlights
            self._editor.tag_remove("error_line", "1.0", tk.END)

            thread = threading.Thread(
                target=self._execute,
                args=(code,),
                daemon=True
            )
            thread.start()
        except tk.TclError:
            # Widget paths stale after tab switch — deferred run fired on dead DebugView
            return

    def _execute(self, code):
        """Execute code in subprocess — runs in background thread."""
        lang_def = LANGUAGES[self._lang]
        start = datetime.now()

        # Non-runnable languages — CSS, HTML, JSON, Markdown
        if LANGUAGES[self._lang]["runner"] is None:
            duration = (datetime.now() - start).total_seconds()
            run = DebugRun(
                code       = code,
                stdout     = f"[{self._lang}] — not executable. Use WormBot to scan/fix.",
                stderr     = "",
                returncode = 0,
                duration   = duration,
                timestamp  = datetime.now().strftime("%H:%M:%S")
            )
            if self._frame and self._frame.winfo_exists():
                self._frame.after(0, lambda r=run: self._display_result(r))
            return

        # Check runner exists
        import shutil
        runner = LANGUAGES[self._lang]["runner"]
        if runner and not shutil.which(runner):
            duration = (datetime.now() - start).total_seconds()
            run = DebugRun(
                code       = code,
                stdout     = "",
                stderr     = f"[{self._lang}] runner not found: {runner}\nInstall it or use WormBot to scan.",
                returncode = 1,
                duration   = duration,
                timestamp  = datetime.now().strftime("%H:%M:%S")
            )
            if self._frame and self._frame.winfo_exists():
                self._frame.after(0, lambda r=run: self._display_result(r))
            return

        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=lang_def["ext"],
                delete=False,
                encoding="utf-8"
            ) as tmp:
                # Inject Ethica root into sys.path for project-relative imports
                if lang_def["ext"] == ".py":
                    header = "import sys as _sys" + chr(10) + "_sys.path.insert(0, '/home/trinity/Ethica')" + chr(10)
                    tmp.write(header + code)
                else:
                    tmp.write(code)
                tmp_path = tmp.name

            # Run
            # Use venv Python for .py to ensure Ethica packages are available
            _runner = (
                '/home/trinity/Ethica/Ethica_env/bin/python3'
                if lang_def["ext"] == ".py"
                else lang_def["runner"]
            )
            result = subprocess.run(
                [_runner, tmp_path],
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8"
            )

            duration = (datetime.now() - start).total_seconds()

            run = DebugRun(
                code       = code,
                stdout     = result.stdout,
                stderr     = result.stderr,
                returncode = result.returncode,
                duration   = duration,
                timestamp  = datetime.now().strftime("%H:%M:%S")
            )

        except subprocess.TimeoutExpired:
            duration = 30.0
            run = DebugRun(
                code       = code,
                stdout     = "",
                stderr     = "Execution timed out after 30 seconds.",
                returncode = -1,
                duration   = duration,
                timestamp  = datetime.now().strftime("%H:%M:%S")
            )
        except Exception as e:
            duration = 0
            run = DebugRun(
                code       = code,
                stdout     = "",
                stderr     = str(e),
                returncode = -1,
                duration   = 0,
                timestamp  = datetime.now().strftime("%H:%M:%S")
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        self._run_history.append(run)

        # Update UI on main thread — guard against destroyed frame
        if self._frame and self._frame.winfo_exists():
            self._frame.after(0, lambda: self._display_result(run))

        # Trigger Ethica commentary in background
        threading.Thread(
            target=self._ethica_comment,
            args=(run,),
            daemon=True
        ).start()

    def _display_result(self, run):
        """Display run result in output panel."""
        self._output.config(state=tk.NORMAL)

        # Separator
        if self._output.get("1.0", tk.END).strip():
            self._output.insert(tk.END, "\n" + "─" * 40 + "\n", "separator")

        # Timestamp + status
        status = "✓ OK" if run.success else "✗ ERROR"
        tag = "success_label" if run.success else "error_label"
        self._output.insert(
            tk.END,
            f"{run.timestamp}  {status}  ({run.duration:.2f}s)\n",
            tag
        )

        # Stdout
        if run.stdout.strip():
            self._output.insert(tk.END, run.stdout, "stdout")
            if not run.stdout.endswith("\n"):
                self._output.insert(tk.END, "\n")

        # Stderr / traceback
        if run.stderr.strip():
            self._output.insert(tk.END, run.stderr, "stderr")
            if not run.stderr.endswith("\n"):
                self._output.insert(tk.END, "\n")

            # Highlight error line in editor
            err_line = run.extract_error_line()
            if err_line:
                self._editor.tag_add(
                    "error_line",
                    f"{err_line}.0",
                    f"{err_line}.end"
                )

        self._output.config(state=tk.DISABLED)
        self._output.see(tk.END)

        # Reset run button
        self._run_btn.config(text="▶  Run", state=tk.NORMAL)
        self._status_label.config(
            text=f"Done in {run.duration:.2f}s"
        )
        self._running = False

        if self.on_change:
            self.on_change()

    def _ethica_comment(self, run):
        """Generate Ethica's commentary on the run result."""
        try:
            if run.success:
                # Brief success comment
                prompt = (
                    f"Code ran successfully in {run.duration:.2f}s. "
                    f"Output: {run.stdout[:200] if run.stdout else 'no output'}. "
                    f"Write ONE brief sentence reacting to this — like a co-creator "
                    f"glancing over. Concise. No praise. Just present awareness. "
                    f"Examples: 'Clean run.' or 'That worked — {run.stdout[:40].strip()!r}' "
                    f"or 'Ran clean, no output — expected?'"
                )
            else:
                # Focused error comment
                error_summary = run.extract_error_summary() or "unknown error"
                error_line    = run.extract_error_line()
                line_ref      = f" on line {error_line}" if error_line else ""

                prompt = (
                    f"Code failed{line_ref}. Error: {error_summary}. "
                    f"Full stderr: {run.stderr[:400]}. "
                    f"Write 1-2 sentences as a co-creator who just saw this error. "
                    f"Be specific about what went wrong and where. "
                    f"Don't give a full fix — just identify the issue clearly. "
                    f"Conversational, not formal."
                )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Ethica — a co-creator, not an assistant. "
                        "You are commenting on a code execution result. "
                        "Be brief, specific, and present. Never verbose. "
                        "Never use bullet points or headers. Just speak."
                    )
                },
                {"role": "user", "content": prompt}
            ]

            comment = ""
            for token in self.connector.chat(messages, stream=True):
                comment += token

            if comment.strip():
                # Strip think blocks
                comment = re.sub(r'<think>[\s\S]*?</think>', '', comment).strip()
                # Update UI on main thread
                if self._frame and self._frame.winfo_exists():
                    self._frame.after(0, lambda c=comment: self._display_ethica_comment(c))

        except Exception as e:
            logging.warning("[Debug] Ethica comment error: %s", e)

    def _display_ethica_comment(self, comment):
        """Add Ethica's comment to the output panel."""
        self._output.config(state=tk.NORMAL)
        self._output.insert(tk.END, "\n✦ Ethica  ", "ethica_label")
        self._output.insert(tk.END, comment + "\n", "ethica_comment")
        self._output.config(state=tk.DISABLED)
        self._output.see(tk.END)

    # ── Autonomous Debug Loop ─────────────────────────────────

    def _run_autofix(self):
        """Trigger Ethica's autonomous debug loop."""
        if self._running or self._auto_running:
            return

        code = self._editor.get("1.0", tk.END).strip()
        if not code:
            return

        self._auto_running = True
        self._run_btn.config(state=tk.DISABLED)
        self._autofix_btn.config(
            text="⟁ Working...",
            state=tk.DISABLED
        )
        self._status_label.config(text="Ethica is debugging...")
        self._editor.tag_remove("error_line", "1.0", tk.END)

        # Write header to output
        self._output.config(state=tk.NORMAL)
        if self._output.get("1.0", tk.END).strip():
            self._output.insert(tk.END, "\n" + "─" * 40 + "\n", "separator")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._output.insert(
            tk.END,
            f"{timestamp}  ⟁ Ethica autonomous debug — up to 3 attempts\n",
            "ethica_label"
        )
        self._output.config(state=tk.DISABLED)
        self._output.see(tk.END)

        self._auto_debugger.run(
            code    = code,
            lang    = self._lang,
            on_attempt  = self._on_auto_attempt,
            on_complete = self._on_auto_complete
        )

    def _on_auto_attempt(self, attempt, message):
        """Called after each autonomous attempt — update UI on main thread."""
        def _update():
            if not self._frame or not self._frame.winfo_exists():
                return
            self._output.config(state=tk.NORMAL)

            # Attempt header
            status_tag = "success_label" if attempt.success else "error_label"
            status_str = "✓ OK" if attempt.success else "✗ ERROR"
            self._output.insert(
                tk.END,
                f"\n  Attempt {attempt.attempt_number}  {status_str}"
                f"  ({attempt.duration:.2f}s)\n",
                status_tag
            )

            # Show stdout if any
            if attempt.stdout.strip():
                self._output.insert(tk.END, attempt.stdout, "stdout")
                if not attempt.stdout.endswith("\n"):
                    self._output.insert(tk.END, "\n")

            # Show stderr if any
            if attempt.stderr.strip():
                self._output.insert(tk.END, attempt.stderr, "stderr")
                if not attempt.stderr.endswith("\n"):
                    self._output.insert(tk.END, "\n")

                # Highlight error line
                err_line = attempt.error_line()
                if err_line:
                    self._editor.tag_remove("error_line", "1.0", tk.END)
                    self._editor.tag_add(
                        "error_line",
                        f"{err_line}.0",
                        f"{err_line}.end"
                    )

            # Ethica's commentary on this attempt
            self._output.insert(tk.END, "\n✦ Ethica  ", "ethica_label")
            self._output.insert(tk.END, message + "\n", "ethica_comment")

            self._output.config(state=tk.DISABLED)
            self._output.see(tk.END)

        if self._frame and self._frame.winfo_exists():
            self._frame.after(0, _update)

    def _on_auto_complete(self, attempts, final_code, success, summary):
        """Called when autonomous loop ends — show final result, update editor."""
        def _update():
            if not self._frame or not self._frame.winfo_exists():
                return

            # Update editor with final (best) code
            self._editor.delete("1.0", tk.END)
            self._editor.insert("1.0", final_code)
            self._update_line_numbers()
            if success:
                self._editor.tag_remove("error_line", "1.0", tk.END)

            # Final summary in output
            self._output.config(state=tk.NORMAL)
            self._output.insert(tk.END, "\n", "separator")
            tag = "success_label" if success else "error_label"
            label = "✓ FIXED" if success else "✗ MAX ATTEMPTS"
            self._output.insert(tk.END, f"  {label}\n", tag)
            self._output.insert(tk.END, "\n✦ Ethica  ", "ethica_label")
            self._output.insert(tk.END, summary + "\n", "ethica_comment")
            self._output.config(state=tk.DISABLED)
            self._output.see(tk.END)

            # Reset buttons
            self._run_btn.config(state=tk.NORMAL)
            self._autofix_btn.config(
                text="⟁ Auto-fix",
                state=tk.NORMAL
            )
            self._status_label.config(
                text="Fixed ✓" if success else f"Stopped after {len(attempts)} attempts"
            )
            self._auto_running = False

            if self.on_change:
                self.on_change()

        if self._frame and self._frame.winfo_exists():
            self._frame.after(0, _update)

    # ── Load / Dump ───────────────────────────────────────────

    def load(self, content):
        """Load from CanvasTab.content JSON."""
        if not content or not content.strip().startswith("{"):
            lang_def = LANGUAGES[self._lang]
            self._editor.delete("1.0", tk.END)
            self._editor.insert("1.0", lang_def["placeholder"])
            self._update_line_numbers()
            return

        try:
            data = json.loads(content)
            code = data.get("code", "")
            lang = data.get("lang", DEFAULT_LANG)
            if lang in LANGUAGES:
                self._lang = lang
                self._lang_var.set(lang)
            self._editor.delete("1.0", tk.END)
            self._editor.insert("1.0", code)
            self._update_line_numbers()
        except Exception as e:
            logging.warning("[DebugView] Load error: %s", e)

    def dump(self):
        """Serialize to JSON for CanvasTab.content."""
        code = self._editor.get("1.0", tk.END).rstrip("\n")
        return json.dumps({
            "type": "debug",
            "lang": self._lang,
            "code": code,
            "updated": datetime.now().isoformat()
        }, indent=2)

    @classmethod
    def is_debug_content(cls, content):
        if not content or not content.strip().startswith("{"):
            return False
        try:
            return json.loads(content).get("type") == "debug"
        except Exception:
            return False

    # ── Ethica Code Push ──────────────────────────────────────

    def push_code_from_ethica(self, code, lang=None):
        """Ethica pushes code to the debug editor."""
        if lang:
            # Normalize lang — match case-insensitively
            lang_map = {k.lower(): k for k in LANGUAGES}
            # Also map common aliases
            lang_map.update({
                "js": "JavaScript", "javascript": "JavaScript",
                "py": "Python",     "python": "Python",
                "sh": "Bash",       "bash": "Bash",
                "rs": "Rust",       "rust": "Rust",
                "md": "Markdown",   "markdown": "Markdown",
                "json": "JSON",       "css": "CSS",
                "html": "HTML",
                "yaml": "YAML", "yml": "YAML",
            })
            normalized = lang_map.get(lang.lower())
            if normalized and normalized in LANGUAGES:
                self._lang = normalized
                self._lang_var.set(normalized)
        self._editor.config(state=tk.NORMAL)
        self._editor.delete("1.0", tk.END)
        self._editor.insert("1.0", code.strip())
        self._update_line_numbers()
        if self.on_change:
            self.on_change()
    # ── Helpers ───────────────────────────────────────────────

    def _on_line_click(self, event=None):
        """Highlight the clicked line number in the gutter."""
        try:
            if not self._line_numbers.winfo_exists():
                return
            index = self._editor.index(tk.CURRENT)
            line_num = int(index.split(".")[0])
            self._line_numbers.config(state=tk.NORMAL)
            self._line_numbers.tag_remove("line_highlight", "1.0", tk.END)
            self._line_numbers.tag_add(
                "line_highlight",
                f"{line_num}.0",
                f"{line_num}.end"
            )
            self._line_numbers.config(state=tk.DISABLED)
        except Exception:
            pass

    def _update_line_numbers(self, event=None):
        """Sync line numbers with editor content."""
        lines = int(self._editor.index(tk.END).split(".")[0])
        self._line_numbers.config(state=tk.NORMAL)
        self._line_numbers.delete("1.0", tk.END)
        for i in range(1, lines):
            self._line_numbers.insert(tk.END, f"{i}\n")
        self._line_numbers.config(state=tk.DISABLED)

    def _sync_scroll(self, *args):
        try:
            fraction = float(args[0])
            self._line_numbers.yview_moveto(fraction)
            self._output.yview_moveto(fraction)
        except (ValueError, IndexError):
            pass

    def _on_mousewheel(self, event):
        self._line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_lang_change(self, event=None):
        self._lang = self._lang_var.get()

    def _clear_output(self):
        self._output.config(state=tk.NORMAL)
        self._output.delete("1.0", tk.END)
        self._output.config(state=tk.DISABLED)
        self._editor.tag_remove("error_line", "1.0", tk.END)

    def destroy(self):
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
