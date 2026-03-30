# ============================================================
# Ethica v0.1 — chat_window.py
# Chat Display — the heart of the UI
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from ui.markdown_renderer import MarkdownRenderer
from modules.notes.notes import note_save as _note_save


class ChatWindow:
    """
    Ethica Chat Window.
    Displays the conversation between user and Ethica.
    Handles message rendering, thinking indicator,
    auto-scroll, and timestamping.
    """

    def __init__(self, parent, theme, config):
        self.parent = parent
        self.theme = theme
        self.config = config
        self._thinking_id = None
        self._thinking_dots = 0
        self._thinking_after = None
        self._last_user_text = ""

        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        """Build the chat display area."""
        c = self.theme.colors

        # Outer frame
        self.frame = tk.Frame(
            self.parent,
            bg=c["bg_chat"]
        )

        # Canvas + scrollbar for scrollable chat
        self.canvas = tk.Canvas(
            self.frame,
            bg=c["bg_chat"],
            highlightthickness=0,
            bd=0
        )

        self.scrollbar = tk.Scrollbar(
            self.frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=c["scrollbar_bg"],
            troughcolor=c["bg_chat"],
            activebackground=c["scrollbar_thumb"],
            width=8
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Inner frame — messages live here
        self.messages_frame = tk.Frame(
            self.canvas,
            bg=c["bg_chat"]
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.messages_frame,
            anchor=tk.NW
        )

        # Pack
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind resize and scroll events
        self.messages_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.messages_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.messages_frame.bind("<Button-4>", self._on_mousewheel)
        self.messages_frame.bind("<Button-5>", self._on_mousewheel)

    # ── Message Rendering ─────────────────────────────────────

    def add_message(self, text, sender="ethica", name=None):
        """
        Add a message bubble to the chat.
        sender: "user" | "ethica" | "system"
        """
        c = self.theme.colors
        f = self.theme.font

        is_user = sender == "user"
        is_system = sender == "system"

        # ── Outer row frame ───────────────────────────────────
        row = tk.Frame(
            self.messages_frame,
            bg=c["bg_chat"],
            pady=4
        )
        row.pack(fill=tk.X, padx=12, pady=2)

        if is_system:
            self._render_system_message(row, text)
            self._scroll_to_bottom()
            return

        # ── Name + timestamp row ──────────────────────────────
        meta_frame = tk.Frame(row, bg=c["bg_chat"])
        meta_frame.pack(
            fill=tk.X,
            anchor=tk.E if is_user else tk.W
        )

        if name:
            name_label = tk.Label(
                meta_frame,
                text=name,
                bg=c["bg_chat"],
                fg=c["accent_bright"] if is_user else c["accent_primary"],
                font=f("body_bold")
            )
            name_label.pack(
                side=tk.RIGHT if is_user else tk.LEFT,
                padx=(0, 4) if is_user else (4, 0)
            )

        if self.config.get("show_timestamps", True):
            ts = datetime.now().strftime("%H:%M")
            ts_label = tk.Label(
                meta_frame,
                text=ts,
                bg=c["bg_chat"],
                fg=c["text_muted"],
                font=f("timestamp")
            )
            ts_label.pack(
                side=tk.RIGHT if is_user else tk.LEFT,
                padx=4
            )

        # ── Bubble frame ──────────────────────────────────────
        bubble_frame = tk.Frame(row, bg=c["bg_chat"])
        bubble_frame.pack(
            anchor=tk.E if is_user else tk.W,
            fill=tk.X
        )

        # Bubble background
        bubble = tk.Frame(
            bubble_frame,
            bg=c["bubble_user"] if is_user else c["bubble_ethica"],
            padx=14,
            pady=10,
            relief=tk.FLAT,
            bd=0
        )

        # Bubble border effect via outer frame
        bubble_border = tk.Frame(
            bubble_frame,
            bg=c["bubble_border"],
            padx=1,
            pady=1
        )
        bubble_border.pack(
            anchor=tk.E if is_user else tk.W,
            padx=(60, 8) if is_user else (8, 60)
        )

        bubble = tk.Frame(
            bubble_border,
            bg=c["bubble_user"] if is_user else c["bubble_ethica"],
            padx=14,
            pady=10
        )
        bubble.pack(fill=tk.BOTH)

        # Dynamic wraplength — chat area width minus margins and padding
        self.canvas.update_idletasks()
        _chat_w = self.canvas.winfo_width()
        _wrap = max(300, _chat_w - 68 - 28)

        # Message content — markdown for Ethica, plain for user
        if is_user:
            self._last_user_text = text
            msg_label = tk.Label(
                bubble,
                text=text,
                bg=c["bubble_user"],
                fg=c["text_user"],
                font=f("body"),
                wraplength=_wrap,
                justify=tk.LEFT,
                anchor=tk.W
            )
            msg_label.pack(fill=tk.X, anchor=tk.W)
            self._bind_quick_note(msg_label, text, "")
        else:
            renderer = MarkdownRenderer(
                bubble, self.theme,
                wraplength=_wrap,
                bg=c["bubble_ethica"]
            )
            renderer.render(text)
            self._bind_quick_note(bubble_border, self._last_user_text, text)

        self._scroll_to_bottom()

    def _bind_quick_note(self, widget, user_text, ethica_text=""):
        """Bind right-click context menu to a bubble widget — Save to Quick Notes."""
        def _show_menu(event):
            menu = tk.Menu(widget, tearoff=0)
            menu.configure(
                bg="#1a1a2e", fg="#e0e0f0",
                activebackground="#333355", activeforeground="#ffffff",
                font=self.theme.font("body"), bd=0, relief=tk.FLAT
            )
            menu.add_command(
                label="⟁ Save to Quick Notes",
                command=lambda: self._save_to_quick_notes(widget, user_text, ethica_text)
            )
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        def _bind_recursive(w):
            w.bind("<Button-3>", _show_menu)
            for child in w.winfo_children():
                _bind_recursive(child)
        _bind_recursive(widget)

    def _save_to_quick_notes(self, widget, user_text, ethica_text=""):
        """Save Q+A pair to Notes module and flash-highlight the widget."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            parts = [f"[Quick Note — {timestamp}]"]
            if user_text.strip():
                parts.append(f"Q: {user_text.strip()}")
            if ethica_text.strip():
                parts.append(f"A: {ethica_text.strip()}")
            note_text = "\n".join(parts)
            _note_save(note_text)
            # Flash green to confirm save
            try:
                original_bg = widget.cget("bg")
                widget.configure(bg="#1a4a2a")
                widget.after(600, lambda: widget.configure(bg=original_bg))
            except Exception:
                pass
        except Exception as e:
            print(f"[QuickNote] save error: {e}")

    def _render_system_message(self, row, text):
        """Render a system/status message — centered, muted."""
        c = self.theme.colors
        f = self.theme.font

        label = tk.Label(
            row,
            text=text,
            bg=c["bg_chat"],
            fg=c["text_muted"],
            font=f("small"),
            wraplength=600,
            justify=tk.CENTER,
            pady=4
        )
        label.pack(anchor=tk.CENTER, padx=20)

        # Subtle separator
        sep = tk.Frame(row, bg=c["separator"], height=1)
        sep.pack(fill=tk.X, padx=40, pady=4)

    # ── Streaming Bubble ──────────────────────────────────────

    def start_stream_bubble(self, name=None):
        """
        Create a live streaming bubble.
        Returns a callable — pass each token to it as it arrives.
        The bubble grows in real time as Ethica thinks out loud.
        """
        c = self.theme.colors
        f = self.theme.font

        # ── Row ───────────────────────────────────────────────
        row = tk.Frame(
            self.messages_frame,
            bg=c["bg_chat"],
            pady=4
        )
        row.pack(fill=tk.X, padx=12, pady=2)

        # ── Meta row — name + timestamp ───────────────────────
        meta_frame = tk.Frame(row, bg=c["bg_chat"])
        meta_frame.pack(fill=tk.X, anchor=tk.W)

        if name:
            tk.Label(
                meta_frame,
                text=name,
                bg=c["bg_chat"],
                fg=c["accent_primary"],
                font=f("body_bold")
            ).pack(side=tk.LEFT, padx=(4, 0))

        if self.config.get("show_timestamps", True):
            ts = datetime.now().strftime("%H:%M")
            tk.Label(
                meta_frame,
                text=ts,
                bg=c["bg_chat"],
                fg=c["text_muted"],
                font=f("timestamp")
            ).pack(side=tk.LEFT, padx=4)

        # ── Bubble ────────────────────────────────────────────
        bubble_frame = tk.Frame(row, bg=c["bg_chat"])
        bubble_frame.pack(anchor=tk.W, fill=tk.X)

        bubble_border = tk.Frame(
            bubble_frame,
            bg=c["bubble_border"],
            padx=1,
            pady=1
        )
        bubble_border.pack(anchor=tk.W, padx=(8, 60))

        bubble = tk.Frame(
            bubble_border,
            bg=c["bubble_ethica"],
            padx=14,
            pady=10
        )
        bubble.pack(fill=tk.BOTH)

        # Live text widget inside bubble — grows with tokens
        stream_text = tk.Text(
            bubble,
            bg=c["bubble_ethica"],
            fg=c["text_ethica"],
            font=f("body"),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            width=60,
            height=1,
            cursor="arrow",
            state=tk.NORMAL,
            highlightthickness=0,
            padx=0,
            pady=0
        )
        stream_text.pack(fill=tk.X, anchor=tk.W)

        self._scroll_to_bottom()

        # ── Token appender ────────────────────────────────────
        def append_token(token):
            """Called with each token as it arrives from Ollama."""
            try:
                stream_text.config(state=tk.NORMAL)
                stream_text.insert(tk.END, token)

                # Auto-resize height to content
                lines = int(stream_text.index(tk.END).split(".")[0])
                stream_text.config(height=max(1, lines - 1))

                stream_text.see(tk.END)
                self._scroll_to_bottom()
            except tk.TclError:
                pass

        def finalize(full_text):
            """
            Called when streaming is complete.
            Replaces live Text widget with rendered markdown.
            Wraplength is dynamic — sized to actual canvas width minus padding.
            """
            try:
                stream_text.destroy()
                canvas_w = self.canvas.winfo_width()
                wrap = max(320, canvas_w - 120) if canvas_w > 10 else 520
                renderer = MarkdownRenderer(
                    bubble, self.theme,
                    wraplength=wrap,
                    bg=c["bubble_ethica"]
                )
                renderer.render(full_text)
                self._bind_quick_note(bubble_border, self._last_user_text, full_text)
                self._scroll_to_bottom()
            except tk.TclError:
                pass

        return append_token, finalize

    # ── Thinking Indicator ────────────────────────────────────

    def show_thinking(self):
        """Show animated thinking indicator."""
        c = self.theme.colors
        f = self.theme.font

        self._thinking_frame = tk.Frame(
            self.messages_frame,
            bg=c["bg_chat"],
            pady=4
        )
        self._thinking_frame.pack(fill=tk.X, padx=12, pady=2)

        self._thinking_label = tk.Label(
            self._thinking_frame,
            text="Ethica is thinking ·",
            bg=c["bg_chat"],
            fg=c["text_muted"],
            font=f("small"),
            anchor=tk.W
        )
        self._thinking_label.pack(anchor=tk.W, padx=8)

        self._thinking_dots = 0
        self._animate_thinking()
        self._scroll_to_bottom()

    def _animate_thinking(self):
        """Animate the thinking dots."""
        if not hasattr(self, '_thinking_label'):
            return

        dots = ["·", "· ·", "· · ·"]
        self._thinking_dots = (self._thinking_dots + 1) % 3

        try:
            self._thinking_label.config(
                text=f"Ethica is thinking {dots[self._thinking_dots]}"
            )
            self._thinking_after = self.parent.after(
                500, self._animate_thinking
            )
        except tk.TclError:
            pass

    def hide_thinking(self):
        """Remove thinking indicator."""
        if self._thinking_after:
            try:
                self.parent.after_cancel(self._thinking_after)
            except Exception:
                pass
            self._thinking_after = None

        if hasattr(self, '_thinking_frame'):
            try:
                self._thinking_frame.destroy()
            except Exception:
                pass

    # ── Scroll ────────────────────────────────────────────────

    def _scroll_to_bottom(self):
        """Auto-scroll to latest message."""
        self.frame.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _on_frame_configure(self, event=None):
        """Update scroll region when messages are added."""
        self.canvas.configure(
            scrollregion=self.canvas.bbox(tk.ALL)
        )

    def _on_canvas_configure(self, event=None):
        """Keep inner frame width in sync with canvas."""
        self.canvas.itemconfig(
            self.canvas_window,
            width=event.width
        )

    def _on_mousewheel(self, event):
        """Handle mouse wheel scroll — cross platform."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(
                int(-1 * (event.delta / 120)), "units"
            )

    # ── Utilities ─────────────────────────────────────────────

    def clear(self):
        """Clear all messages from the chat window."""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

    # ── Live Theme Refresh ────────────────────────────────────

    def apply_theme(self):
        """
        Repaint all chat window elements with current theme.
        Called automatically by ThemeEngine on theme switch.
        """
        c = self.theme.colors

        self.frame.config(bg=c["bg_chat"])
        self.canvas.config(bg=c["bg_chat"])
        self.messages_frame.config(bg=c["bg_chat"])
        self.scrollbar.config(
            bg=c["scrollbar_bg"],
            troughcolor=c["bg_chat"],
            activebackground=c["scrollbar_thumb"]
        )

        # Repaint all existing message rows
        for widget in self.messages_frame.winfo_children():
            self._repaint_widget(widget, c)

    def _repaint_widget(self, widget, c):
        """Recursively repaint a widget and its children."""
        try:
            wtype = widget.winfo_class()
            if wtype in ("Frame",):
                widget.config(bg=c["bg_chat"])
            elif wtype == "Label":
                widget.config(bg=c["bg_chat"], fg=c["text_muted"])
        except Exception:
            pass
        for child in widget.winfo_children():
            self._repaint_widget(child, c)
