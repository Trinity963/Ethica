# ============================================================
# Ethica v0.1 — scroll_drop.py
# Scroll Drop Zone — drag a file, Ethica picks it up
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Drop a file onto this zone — Ethica reads it,
# WormBot scans it, result goes straight to canvas.
# Chat stays clean. Always.
# ============================================================

import tkinter as tk
import os

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".css", ".html", ".htm", ".rs",
    ".json", ".md", ".txt", ".yaml", ".yml", ".pdf",
    ".png", ".jpg", ".jpeg",
    ".zip"
}


class ScrollDrop:
    """
    Scroll Drop Zone.
    Sits above the input bar.
    V drags a file — Ethica picks it up instantly.
    """

    def __init__(self, parent, theme, config, on_file_drop):
        self.parent       = parent
        self.theme        = theme
        self.config       = config
        self.on_file_drop = on_file_drop
        self._build()

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self.frame = tk.Frame(
            self.parent,
            bg=c["bg_secondary"],
            padx=12,
            pady=4,
        )

        self._zone = tk.Frame(
            self.frame,
            bg=c["bg_secondary"],
            padx=8,
            pady=6,
            cursor="hand2",
        )
        self._zone.pack(fill=tk.X)

        self._canvas = tk.Canvas(
            self._zone,
            height=38,
            bg=c["bg_secondary"],
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.X)

        self._label = tk.Label(
            self._canvas,
            text="⟁  Drop file — Ethica picks it up",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            cursor="hand2",
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")

        self._canvas.bind("<Configure>", self._draw_border)
        self._canvas.bind("<Enter>",     self._on_hover_enter)
        self._canvas.bind("<Leave>",     self._on_hover_leave)
        self._label.bind("<Enter>",      self._on_hover_enter)
        self._label.bind("<Leave>",      self._on_hover_leave)

        if DND_AVAILABLE:
            try:
                self._canvas.drop_target_register(DND_FILES)
                self._canvas.dnd_bind("<<Drop>>",      self._on_drop)
                self._canvas.dnd_bind("<<DragEnter>>", self._on_drag_enter)
                self._canvas.dnd_bind("<<DragLeave>>", self._on_drag_leave)
                self._label.drop_target_register(DND_FILES)
                self._label.dnd_bind("<<Drop>>",       self._on_drop)
                self._label.dnd_bind("<<DragEnter>>",  self._on_drag_enter)
                self._label.dnd_bind("<<DragLeave>>",  self._on_drag_leave)
            except Exception:
                pass
        else:
            self._canvas.bind("<Button-1>", self._browse_file)
            self._label.bind("<Button-1>",  self._browse_file)
            self._label.config(text="⟁  Click to pick a file — Ethica picks it up")

    def reregister_drop(self):
        """Re-register DND targets — call after any new Toplevel is created."""
        if not DND_AVAILABLE:
            return
        try:
            if not self._canvas.winfo_exists() or not self._label.winfo_exists():
                return
            self._canvas.drop_target_register(DND_FILES)
            self._canvas.dnd_bind("<<Drop>>",      self._on_drop)
            self._canvas.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self._canvas.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            self._label.drop_target_register(DND_FILES)
            self._label.dnd_bind("<<Drop>>",       self._on_drop)
            self._label.dnd_bind("<<DragEnter>>",  self._on_drag_enter)
            self._label.dnd_bind("<<DragLeave>>",  self._on_drag_leave)
        except Exception:
            pass

    def _draw_border(self, event=None, color=None):
        c   = self.theme.colors
        col = color or c.get("accent_soft", "#6b3fa0")
        w   = self._canvas.winfo_width()
        h   = self._canvas.winfo_height()
        self._canvas.delete("border")
        self._canvas.create_rectangle(
            2, 2, w-2, h-2,
            outline=col, dash=(4,4), width=1, tags="border"
        )

    def _on_hover_enter(self, event=None):
        c = self.theme.colors
        self._draw_border(color=c.get("accent", "#9b59b6"))
        self._label.config(fg=c.get("accent", "#9b59b6"))

    def _on_hover_leave(self, event=None):
        c = self.theme.colors
        self._draw_border(color=c.get("accent_soft", "#6b3fa0"))
        self._label.config(fg=c.get("text_muted", "#888"))

    def _on_drag_enter(self, event=None):
        c = self.theme.colors
        self._canvas.config(bg=c.get("bg_hover", "#2a1a3a"))
        self._label.config(
            bg=c.get("bg_hover", "#2a1a3a"),
            fg=c.get("accent", "#9b59b6"),
            text="⟁  Release to scan"
        )
        self._draw_border(color=c.get("accent", "#9b59b6"))

    def _on_drag_leave(self, event=None):
        c = self.theme.colors
        self._canvas.config(bg=c.get("bg_secondary", "#1a0a2e"))
        self._label.config(
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c.get("text_muted", "#888"),
            text="⟁  Drop file — Ethica picks it up"
        )
        self._draw_border()

    def _on_drop(self, event):
        self._on_drag_leave()
        raw = event.data.strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        filepath = raw.strip()
        if not os.path.isfile(filepath):
            self._flash_error("File not found")
            return
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            self._flash_error(f"Unsupported: {ext}")
            return
        filename = os.path.basename(filepath)
        self._flash_success(f"⟁  {filename}")
        if self.on_file_drop:
            self.on_file_drop(filepath)
        # Re-register after every drop — Toplevel creation can break DND bindings
        self.parent.after(200, self.reregister_drop)

    def _browse_file(self, event=None):
        from tkinter import filedialog
        ext_list = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        filepath = filedialog.askopenfilename(
            title="Pick a file for Ethica",
            filetypes=[("Code files", ext_list), ("All files", "*.*")]
        )
        if filepath:
            self._flash_success(f"⟁  {os.path.basename(filepath)}")
            if self.on_file_drop:
                self.on_file_drop(filepath)

    def _flash_success(self, text):
        c = self.theme.colors
        self._label.config(text=text, fg=c.get("accent", "#9b59b6"))
        self._draw_border(color=c.get("accent", "#9b59b6"))
        self._canvas.after(2000, self._reset_label)

    def _flash_error(self, text):
        self._label.config(text=f"✗  {text}", fg="#e74c3c")
        self._draw_border(color="#e74c3c")
        self._canvas.after(2000, self._reset_label)

    def _reset_label(self):
        c = self.theme.colors
        self._label.config(
            text="⟁  Drop file — Ethica picks it up",
            fg=c.get("text_muted", "#888")
        )
        self._draw_border()

    def apply_theme(self, theme):
        self.theme = theme
        c = theme.colors
        self.frame.config(bg=c["bg_secondary"])
        self._zone.config(bg=c["bg_secondary"])
        self._canvas.config(bg=c["bg_secondary"])
        self._label.config(bg=c["bg_secondary"], fg=c["text_muted"])
        self._draw_border()
