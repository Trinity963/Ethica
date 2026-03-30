# ============================================================
# Ethica v0.1 — input_bar.py
# User Input Bar — where the conversation begins
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk


class InputBar:
    """
    Ethica Input Bar.
    Where the user speaks.
    - Multi-line input with auto-grow
    - Enter to send, Shift+Enter for new line
    - Send button
    - Disabled state while Ethica is thinking
    - Placeholder text
    """

    PLACEHOLDER = "Speak your mind..."

    def __init__(self, parent, theme, config, on_send):
        self.parent = parent
        self.theme = theme
        self.config = config
        self.on_send = on_send
        self._placeholder_active = False
        self._enabled = True

        self._build()
        self._show_placeholder()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        """Build the input bar."""
        c = self.theme.colors
        f = self.theme.font

        # Outer frame
        self.frame = tk.Frame(
            self.parent,
            bg=c["bg_secondary"],
            pady=10,
            padx=12
        )

        # Inner container — input + button side by side
        inner = tk.Frame(
            self.frame,
            bg=c["bg_input"],
            padx=2,
            pady=2
        )
        inner.pack(fill=tk.X)

        # Border frame
        border = tk.Frame(
            self.frame,
            bg=c["accent_soft"],
            padx=1,
            pady=1
        )
        border.pack(fill=tk.X)

        input_container = tk.Frame(
            border,
            bg=c["bg_input"]
        )
        input_container.pack(fill=tk.X)

        # ── Text input ────────────────────────────────────────
        self.text_input = tk.Text(
            input_container,
            bg=c["bg_input"],
            fg=c["text_muted"],        # starts muted for placeholder
            font=f("input"),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            height=2,
            padx=12,
            pady=10,
            insertbackground=c["accent_bright"],   # cursor color
            selectbackground=c["accent_glow"],
            selectforeground=c["text_primary"],
            highlightthickness=0
        )
        self.text_input.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        # ── Send button ───────────────────────────────────────
        self.send_btn = tk.Button(
            input_container,
            text="  ➤  ",
            bg=c["button_bg"],
            fg=c["button_text"],
            font=f("button"),
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=10,
            cursor="hand2",
            activebackground=c["button_hover"],
            activeforeground=c["button_text"],
            command=self._send
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # ── Hint label ────────────────────────────────────────
        hint = tk.Label(
            self.frame,
            text="Enter to send  ·  Shift+Enter for new line",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("timestamp")
        )
        hint.pack(anchor=tk.E, pady=(4, 0))

        # ── Bindings ──────────────────────────────────────────
        self.text_input.bind("<Return>", self._on_enter)
        self.text_input.bind("<Shift-Return>", self._on_shift_enter)
        self.text_input.bind("<FocusIn>", self._on_focus_in)
        self.text_input.bind("<FocusOut>", self._on_focus_out)
        self.text_input.bind("<KeyRelease>", self._on_key_release)

        # Button hover effects
        self.send_btn.bind("<Enter>", self._btn_hover_in)
        self.send_btn.bind("<Leave>", self._btn_hover_out)

    # ── Placeholder ───────────────────────────────────────────

    def _show_placeholder(self):
        """Show placeholder text in muted color."""
        c = self.theme.colors
        self._placeholder_active = True
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", self.PLACEHOLDER)
        self.text_input.config(fg=c["text_muted"])

    def _clear_placeholder(self):
        """Remove placeholder when user starts typing."""
        c = self.theme.colors
        if self._placeholder_active:
            self.text_input.delete("1.0", tk.END)
            self.text_input.config(fg=c["text_primary"])
            self._placeholder_active = False

    # ── Send Logic ────────────────────────────────────────────

    def _send(self):
        """Extract message and fire on_send callback."""
        if not self._enabled:
            return

        text = self.text_input.get("1.0", tk.END).strip()

        if not text or text == self.PLACEHOLDER:
            return

        # Clear input
        self.text_input.delete("1.0", tk.END)
        self._show_placeholder()

        # Fire callback
        self.on_send(text)

    # ── Event Handlers ────────────────────────────────────────

    def _on_enter(self, event):
        """Enter key — send message."""
        self._send()
        return "break"   # prevent default newline

    def _on_shift_enter(self, event):
        """Shift+Enter — insert newline."""
        return None       # allow default behavior

    def _on_focus_in(self, event):
        """Clear placeholder on focus — check actual content, not just flag."""
        current = self.text_input.get("1.0", tk.END).strip()
        if current == self.PLACEHOLDER or self._placeholder_active:
            self._clear_placeholder()

    def _on_focus_out(self, event):
        """Restore placeholder if empty."""
        current = self.text_input.get("1.0", tk.END).strip()
        if not current:
            self._show_placeholder()

    def _on_key_release(self, event):
        """Auto-grow input height with content."""
        lines = int(self.text_input.index(tk.END).split(".")[0])
        new_height = max(2, min(lines, 6))   # min 2, max 6 lines
        self.text_input.config(height=new_height)

    def _btn_hover_in(self, event):
        """Button hover — brighten."""
        if self._enabled:
            self.send_btn.config(bg=self.theme.get("button_hover"))

    def _btn_hover_out(self, event):
        """Button hover out — restore."""
        if self._enabled:
            self.send_btn.config(bg=self.theme.get("button_bg"))

    # ── State ─────────────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        """Enable or disable input while Ethica is responding."""
        c = self.theme.colors
        self._enabled = enabled

        if enabled:
            self.text_input.config(state=tk.NORMAL)
            self.send_btn.config(
                state=tk.NORMAL,
                bg=c["button_bg"],
                cursor="hand2"
            )
            self.text_input.focus_set()
        else:
            self.text_input.config(state=tk.DISABLED)
            self.send_btn.config(
                state=tk.DISABLED,
                bg=c["accent_soft"],
                cursor="arrow"
            )

    def insert_text(self, text):
        """Insert text into the input field — used by Tool Lister."""
        self._clear_placeholder()
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", text)
        self.text_input.focus_set()

    def focus(self):
        """Set focus to input field."""
        self.text_input.focus_set()

    # ── Live Theme Refresh ────────────────────────────────────

    def apply_theme(self):
        """
        Repaint input bar with current theme colors.
        Called automatically by ThemeEngine on theme switch.
        """
        c = self.theme.colors

        self.frame.config(bg=c["bg_secondary"])
        self.text_input.config(
            bg=c["bg_input"],
            fg=c["text_primary"] if not self._placeholder_active else c["text_muted"],
            insertbackground=c["accent_bright"],
            selectbackground=c["accent_glow"],
            selectforeground=c["text_primary"]
        )
        self.send_btn.config(
            bg=c["button_bg"] if self._enabled else c["accent_soft"],
            fg=c["button_text"],
            activebackground=c["button_hover"],
            activeforeground=c["button_text"]
        )
