# ============================================================
# Ethica v0.1 — settings_view.py
# Settings UI — edit config/settings.json from inside Ethica
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import os
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

CONFIG_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "config" / "settings.json"

SETTINGS_SCHEMA = [
    {
        "section": "Identity",
        "fields": [
            {"key": "user_name",    "label": "Your name",     "type": "text"},
            {"key": "ethica_name",  "label": "Ethica's name", "type": "text"},
        ]
    },
    {
        "section": "Model",
        "fields": [
            {"key": "model",        "label": "Active model",  "type": "text"},
            {"key": "ollama_host",  "label": "Ollama host",   "type": "text"},
            {"key": "models_dir",   "label": "Models folder", "type": "path"},
        ]
    },
    {
        "section": "Appearance",
        "fields": [
            {"key": "theme",        "label": "Theme",         "type": "choice",
             "options": ["purple", "midnight", "forest", "ember", "arctic"]},
            {"key": "font_size",    "label": "Font size",     "type": "int"},
        ]
    },
    {
        "section": "Behaviour",
        "fields": [
            {"key": "stream_responses", "label": "Stream responses", "type": "bool"},
            {"key": "show_timestamps",  "label": "Show timestamps",  "type": "bool"},
        ]
    },
    {
        "section": "Window",
        "fields": [
            {"key": "window_width",  "label": "Window width",  "type": "int"},
            {"key": "window_height", "label": "Window height", "type": "int"},
        ]
    },
]


class SettingsView:
    def __init__(self, parent, theme, config, on_save=None):
        self.parent   = parent
        self.theme    = theme
        self.config   = config          # dict — live config
        self.on_save  = on_save         # callback(updated_config)
        self._frame   = None
        self._vars    = {}              # key → tk variable
        self._status  = None
        self._build()

    # ── Build ──────────────────────────────────────────────────

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._frame = tk.Frame(self.parent, bg=c["bg_primary"])
        self._frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(self._frame, bg=c["bg_primary"], pady=12, padx=16)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="⚙ Settings",
            bg=c["bg_primary"],
            fg=c["text_primary"],
            font=f("heading"),
        ).pack(side=tk.LEFT)

        tk.Button(
            header,
            text="✓ Save",
            bg=c.get("accent", "#9b59b6"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=12, pady=4,
            cursor="hand2",
            command=self._save
        ).pack(side=tk.RIGHT)

        tk.Frame(self._frame, bg=c.get("border", "#3a1a5a"), height=1).pack(fill=tk.X, padx=16)

        # Scrollable content
        container = tk.Frame(self._frame, bg=c["bg_primary"])
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=c["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._scroll_frame = tk.Frame(canvas, bg=c["bg_primary"])
        self._canvas_window = canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")

        self._scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._canvas_window, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Build sections
        for section in SETTINGS_SCHEMA:
            self._build_section(section, c, f)

        # Status bar
        self._status = tk.Label(
            self._frame,
            text="",
            bg=c["bg_primary"],
            fg=c.get("accent", "#9b59b6"),
            font=f("small"),
            pady=8
        )
        self._status.pack(fill=tk.X, padx=16)

    def _build_section(self, section, c, f):
        sec_frame = tk.Frame(self._scroll_frame, bg=c["bg_primary"], padx=16, pady=8)
        sec_frame.pack(fill=tk.X)

        tk.Label(
            sec_frame,
            text=section["section"],
            bg=c["bg_primary"],
            fg=c.get("accent", "#9b59b6"),
            font=f("small"),
        ).pack(anchor="w", pady=(4, 2))

        card = tk.Frame(sec_frame, bg=c.get("bg_secondary", "#1a0a2e"), padx=16, pady=10)
        card.pack(fill=tk.X)

        for field in section["fields"]:
            self._build_field(card, field, c, f)

    def _build_field(self, parent, field, c, f):
        key     = field["key"]
        label   = field["label"]
        ftype   = field["type"]
        current = self.config.get(key, "")

        row = tk.Frame(parent, bg=c.get("bg_secondary", "#1a0a2e"), pady=4)
        row.pack(fill=tk.X)

        tk.Label(
            row,
            text=label,
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_muted"],
            font=f("small"),
            width=20,
            anchor="w"
        ).pack(side=tk.LEFT)

        if ftype == "bool":
            var = tk.BooleanVar(value=bool(current))
            tk.Checkbutton(
                row,
                variable=var,
                bg=c.get("bg_secondary", "#1a0a2e"),
                fg=c["text_primary"],
                selectcolor=c.get("bg_secondary", "#1a0a2e"),
                activebackground=c.get("bg_secondary", "#1a0a2e"),
                cursor="hand2"
            ).pack(side=tk.LEFT)
            self._vars[key] = var

        elif ftype == "choice":
            var = tk.StringVar(value=str(current))
            opts = field.get("options", [])
            tk.OptionMenu(row, var, *opts).configure(
                bg=c.get("bg_primary", "#0d0d1a"),
                fg=c["text_primary"],
                activebackground=c.get("accent_soft", "#2a0a4e"),
                activeforeground=c["text_primary"],
                relief=tk.FLAT,
                font=f("small"),
                highlightthickness=0
            )
            om = tk.OptionMenu(row, var, *opts)
            om.configure(
                bg=c.get("bg_primary", "#0d0d1a"),
                fg=c["text_primary"],
                relief=tk.FLAT,
                font=f("small"),
                highlightthickness=0
            )
            om.pack(side=tk.LEFT)
            self._vars[key] = var

        elif ftype == "path":
            var = tk.StringVar(value=str(current))
            tk.Entry(
                row,
                textvariable=var,
                bg=c.get("bg_primary", "#0d0d1a"),
                fg=c["text_primary"],
                insertbackground=c["text_primary"],
                font=f("small"),
                relief=tk.FLAT,
                width=40
            ).pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(
                row,
                text="Browse",
                bg=c.get("button_bg", "#4a1a6a"),
                fg=c.get("button_text", "#ffffff"),
                font=f("small"),
                relief=tk.FLAT,
                padx=6, pady=1,
                cursor="hand2",
                command=lambda v=var: self._browse_dir(v)
            ).pack(side=tk.LEFT)
            self._vars[key] = var

        elif ftype == "int":
            var = tk.StringVar(value=str(current))
            tk.Entry(
                row,
                textvariable=var,
                bg=c.get("bg_primary", "#0d0d1a"),
                fg=c["text_primary"],
                insertbackground=c["text_primary"],
                font=f("small"),
                relief=tk.FLAT,
                width=8
            ).pack(side=tk.LEFT)
            self._vars[key] = var

        else:  # text
            var = tk.StringVar(value=str(current))
            tk.Entry(
                row,
                textvariable=var,
                bg=c.get("bg_primary", "#0d0d1a"),
                fg=c["text_primary"],
                insertbackground=c["text_primary"],
                font=f("small"),
                relief=tk.FLAT,
                width=40
            ).pack(side=tk.LEFT)
            self._vars[key] = var

    # ── Actions ────────────────────────────────────────────────

    def _browse_dir(self, var):
        path = filedialog.askdirectory(title="Select folder")
        if path:
            var.set(path)

    def _save(self):
        updated = self.config.all() if hasattr(self.config, "all") else dict(self.config)
        for key, var in self._vars.items():
            val = var.get()
            # Coerce types
            if isinstance(self.config.get(key), bool):
                updated[key] = bool(val)
            elif isinstance(self.config.get(key), int):
                try:
                    updated[key] = int(val)
                except ValueError:
                    self._status.config(text=f"⚠ {key} must be a number")
                    return
            else:
                updated[key] = val

        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(updated, f, indent=2)
            # Update live config via set()
            for k, v in updated.items():
                if hasattr(self.config, 'set'):
                    self.config.set(k, v)
            self._status.config(text="✓ Settings saved — restart to apply model/theme changes")
            if self.on_save:
                self.on_save(updated)
        except Exception as e:
            self._status.config(text=f"⚠ Save failed: {e}")

    # ── Lifecycle ──────────────────────────────────────────────

    def destroy(self):
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
