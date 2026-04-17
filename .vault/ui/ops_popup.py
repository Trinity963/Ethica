# ============================================================
# Ethica v0.1 — ops_popup.py
# Ops Popup — all tool output routes here, chat stays clean
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Tool results land here — not in chat.
# Chat stays V↔Ethica conversation only.
# Brief marker in chat: "⟁ guardian start → Ops"
# ============================================================

import re
import tkinter as tk
from datetime import datetime
from pathlib import Path


class OpsPopup:
    """
    Floating ops window — shows all tool output.
    Persists across tool calls. Auto-scrolls to latest.
    """

    def __init__(self, parent, theme, config):
        self.parent = parent
        self.theme = theme
        self.config = config
        self._win = None
        self._log = None      # tk.Text widget
        self._entry_count = 0
        self._canvas_ref = None   # Set by main_window after canvas init
        self._build()

    # ── Build ──────────────────────────────────────────────────

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._win = tk.Toplevel(self.parent)
        self._win.title("⟁ Ops")
        self._win.geometry("720x460+60+60")
        self._win.configure(bg=c["bg_primary"])
        self._win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Header
        header = tk.Frame(self._win, bg=c["bg_primary"], pady=8, padx=12)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="⟁ Ops",
            bg=c["bg_primary"],
            fg=c["text_primary"],
            font=f("heading"),
        ).pack(side=tk.LEFT)

        tk.Button(
            header,
            text="Clear",
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            padx=8, pady=2,
            cursor="hand2",
            command=self.clear
        ).pack(side=tk.RIGHT)

        tk.Button(
            header,
            text="✕ Close",
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            padx=8, pady=2,
            cursor="hand2",
            command=self._on_close
        ).pack(side=tk.RIGHT, padx=(0, 6))

        tk.Frame(self._win, bg=c.get("border", "#3a1a5a"), height=1).pack(fill=tk.X)

        # Log area
        log_frame = tk.Frame(self._win, bg=c["bg_primary"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._log = tk.Text(
            log_frame,
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
            padx=12,
            pady=8,
            cursor="arrow",
            spacing1=2,
            spacing3=4,
        )
        self._log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._log.yview)

        # Tag styles
        self._log.tag_configure("timestamp",
                                foreground=c.get("text_muted", "#888888"),
                                font=f("small"))
        self._log.tag_configure("tool_name",
                                foreground=c.get("accent", "#9b59b6"),
                                font=f("small"))
        self._log.tag_configure("result",
                                foreground=c["text_primary"],
                                font=f("small"))
        self._log.tag_configure("filepath",
                                foreground="#c792ea", underline=True)
        self._log.tag_configure("separator",
                                foreground=c.get("border", "#3a1a5a"),
                                font=f("small"))
        self._log.tag_configure("error",
                                foreground="#e74c3c",
                                font=f("small"))
        self._log.tag_configure("hyperlink",
                                foreground="#7eb8f7", underline=True)
        self._log.tag_bind("hyperlink", "<Button-1>", self._open_url)
        self._log.tag_bind("hyperlink", "<Enter>",
                           lambda e: self._log.config(cursor="hand2"))
        self._log.tag_bind("hyperlink", "<Leave>",
                           lambda e: self._log.config(cursor="arrow"))
        self._log.tag_configure("filelink",
                                foreground="#f7c97e", underline=True)
        self._log.tag_bind("filelink", "<Button-1>", self._open_file_in_canvas)
        self._log.tag_bind("filelink", "<Enter>",
                           lambda e: self._log.config(cursor="hand2"))
        self._log.tag_bind("filelink", "<Leave>",
                           lambda e: self._log.config(cursor="arrow"))

    # ── Public API ─────────────────────────────────────────────

    def set_canvas(self, canvas):
        """Called by main_window to give Ops a canvas reference."""
        self._canvas_ref = canvas

    def _open_url(self, event):
        """Open clicked URL in system browser."""
        import webbrowser
        index = self._log.index(f"@{event.x},{event.y}")
        tag_ranges = self._log.tag_ranges("hyperlink")
        for i in range(0, len(tag_ranges), 2):
            start = tag_ranges[i]
            end = tag_ranges[i + 1]
            if self._log.compare(start, "<=", index) and self._log.compare(index, "<=", end):
                url = self._log.get(start, end).strip()
                webbrowser.open(url)
                break

    def _tag_urls_in_log(self):
        """Scan log content and apply hyperlink tag to all URLs."""
        self._log.tag_remove("hyperlink", "1.0", tk.END)
        pattern = re.compile(r'https?://\S+')
        line_count = int(self._log.index(tk.END).split('.')[0])
        for lineno in range(1, line_count + 1):
            line = self._log.get(f"{lineno}.0", f"{lineno}.end")
            for match in pattern.finditer(line):
                start_idx = f"{lineno}.{match.start()}"
                end_idx = f"{lineno}.{match.end()}"
                self._log.tag_add("hyperlink", start_idx, end_idx)

    def _open_file_in_canvas(self, event):
        """Open clicked local file path in canvas — routes by extension."""
        index = self._log.index(f"@{event.x},{event.y}")
        tag_ranges = self._log.tag_ranges("filelink")
        for i in range(0, len(tag_ranges), 2):
            start = tag_ranges[i]
            end = tag_ranges[i + 1]
            if self._log.compare(start, "<=", index) and self._log.compare(index, "<=", end):
                path_str = self._log.get(start, end).strip().strip('`\'\"')
                p = Path(path_str).expanduser().resolve()
                if not p.exists():
                    return
                if p.is_dir():
                    import subprocess, sys
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, str(p)])
                    return
                if self._canvas_ref:
                    self._canvas_ref.open_file(str(p))
                break

    def _tag_filepaths_in_log(self):
        """Scan log content and apply filelink tag to local file paths."""
        self._log.tag_remove("filelink", "1.0", tk.END)
        pattern = re.compile(r'`?/home/[\w/._\- ]+(?= —)`?|`?/home/[\w/._-]+`?|`?~/[\w/._-]+`?')
        line_count = int(self._log.index(tk.END).split('.')[0])
        for lineno in range(1, line_count + 1):
            line = self._log.get(f"{lineno}.0", f"{lineno}.end")
            for match in pattern.finditer(line):
                path_str = match.group()
                # Only linkify if it looks like a real file (has an extension or is a known path)
                if '.' in path_str.split('/')[-1] or path_str.count('/') > 2:
                    start_idx = f"{lineno}.{match.start()}"
                    end_idx = f"{lineno}.{match.end()}"
                    self._log.tag_add("filelink", start_idx, end_idx)

    def _insert_tree_result(self, result):
        """Render fm_tree output with clickable file lines."""

        # Extract root path from header line: "FileManager Tree — /path/to/dir"
        root_path = None
        lines = result.split("\n")
        for line in lines:
            if line.startswith("FileManager Tree"):
                m = re.search(r"FileManager Tree — (.+)", line)
                if m:
                    root_path = Path(m.group(1).strip())
                break

        # Walk lines — make 📄 lines clickable, rest plain
        for line in lines:
            if "📄" in line:
                # Extract filename after icon
                m = re.search(r"📄 (.+)", line)
                if m and root_path:
                    filename = m.group(1).strip()
                    # Reconstruct approximate full path by searching under root
                    tag_name = f"fp_{self._entry_count}_{filename}"
                    self._log.tag_configure(tag_name,
                                            foreground="#c792ea", underline=True)

                    def _make_open(fn, rp, tn):
                        def _open_in_canvas(event=None):
                            # Search for file under root path
                            found = None
                            for p in rp.rglob(fn):
                                found = p
                                break
                            if not found:
                                return
                            try:
                                text = found.read_text(encoding="utf-8", errors="ignore")
                            except Exception:
                                return
                            if self._canvas_ref:
                                self._canvas_ref._drop_as_document(text, fn)
                            self._log.tag_configure(tn, foreground="#7ec8a0")
                        return _open_in_canvas

                    # Insert prefix (tree chars) as plain, filename as clickable
                    prefix = re.sub(r"📄.*", "", line)
                    self._log.insert(tk.END, prefix + "📄 ", "result")
                    self._log.insert(tk.END, filename, (tag_name,))
                    self._log.insert(tk.END, "\n", "result")
                    self._log.tag_bind(tag_name, "<Button-1>",
                                       _make_open(filename, root_path, tag_name))
                    self._log.tag_bind(tag_name, "<Enter>",
                                       lambda e, t=tag_name: self._log.config(cursor="hand2"))
                    self._log.tag_bind(tag_name, "<Leave>",
                                       lambda e: self._log.config(cursor=""))
                else:
                    self._log.insert(tk.END, line + "\n", "result")
            else:
                self._log.insert(tk.END, line + "\n", "result")

    def push(self, tool_name, result):
        """Add a tool result entry to the ops log."""
        if not self._win or not self._win.winfo_exists():
            self._build()

        ts = datetime.now().strftime("%H:%M:%S")
        is_error = result.startswith("⚠") or "error" in result.lower()[:30]

        self._log.config(state=tk.NORMAL)

        if self._entry_count > 0:
            self._log.insert(tk.END, "─" * 60 + "\n", "separator")

        self._log.insert(tk.END, f"{ts}  ", "timestamp")
        self._log.insert(tk.END, f"⟁ {tool_name}\n", "tool_name")

        # fm_tree — render file lines as clickable canvas openers
        if "fm_tree" in tool_name.lower() or result.startswith("FileManager Tree"):
            self._insert_tree_result(result.strip())
        else:
            self._log.insert(tk.END, result.strip() + "\n", "error" if is_error else "result")

        # 📋 Copy button for this entry
        _c = self.theme.colors
        _f = self.theme.font
        _snap = result.strip()

        def _make_copy(text):
            def _copy():
                self._win.clipboard_clear()
                self._win.clipboard_append(text)
                _btn.config(text="✓ Copied")
                self._win.after(1500, lambda: _btn.config(text="📋 Copy"))
            _btn = tk.Button(
                self._win,
                text="📋 Copy",
                bg=_c.get("bg_secondary", "#1a0a2e"),
                fg=_c.get("text_muted", "#888888"),
                font=_f("small"),
                relief=tk.FLAT, padx=6, pady=1,
                cursor="hand2", command=_copy
            )
            return _btn
        _btn = _make_copy(_snap)
        self._log.window_create(tk.END, window=_btn)
        self._log.insert(tk.END, "\n")
        self._tag_urls_in_log()
        self._tag_filepaths_in_log()
        self._log.config(state=tk.DISABLED)
        self._log.see(tk.END)
        self._entry_count += 1

        # Bring to front
        self._win.deiconify()
        self._win.lift()

    def clear(self):
        """Clear the ops log."""
        self._log.config(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.config(state=tk.DISABLED)
        self._entry_count = 0

    def show(self):
        """Show/raise the ops window."""
        if not self._win or not self._win.winfo_exists():
            self._build()
        self._win.deiconify()
        self._win.lift()

    def hide(self):
        """Hide the ops window without destroying."""
        if self._win and self._win.winfo_exists():
            self._win.withdraw()

    def is_visible(self):
        return bool(self._win and self._win.winfo_exists()
                    and self._win.state() != "withdrawn")

    def destroy(self):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    def _on_close(self):
        """Hide on close — don't destroy, keep log alive."""
        self.hide()