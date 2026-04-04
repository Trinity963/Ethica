# ============================================================
# Ethica v0.1 — sidebar.py
# Sidebar — Control Surface
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import logging
import tkinter as tk
from tkinter import ttk
from ui.memory_search import MemorySearchWindow
from ui.tool_lister import ToolListerWindow


class Sidebar:
    """
    Ethica Sidebar.
    The user's control surface.
    - Model selector
    - Theme selector
    - User name / Ethica name config
    - New conversation button
    - About section
    """

    def __init__(self, parent, theme, config,
                     on_theme_change=None, on_model_change=None, on_new_conversation=None,
                     on_save_toggle=None, on_open_file=None, on_name_save=None):
        self.parent = parent
        self.theme = theme
        self.config = config
        self.on_theme_change = on_theme_change
        self.on_model_change = on_model_change
        self.on_new_conversation = on_new_conversation
        self.on_save_toggle = on_save_toggle
        self.on_open_file = on_open_file
        self.on_name_save = on_name_save
        self._save_chat = tk.BooleanVar(value=False)

        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        """Build the sidebar."""
        c = self.theme.colors

        # Outer frame — fixed width
        self.frame = tk.Frame(
            self.parent,
            bg=c["bg_secondary"],
            width=200
        )
        self.frame.pack_propagate(False)

        # ── Ethica glyph / identity ───────────────────────────
        self._build_identity()

        # ── Separator ─────────────────────────────────────────
        self._separator()

        # ── Model selector ────────────────────────────────────
        self._build_section("MODEL")
        self._build_model_selector()

        # ── Separator ─────────────────────────────────────────
        self._separator()

        # ── Theme selector ────────────────────────────────────
        self._build_section("THEME")
        self._build_theme_selector()

        # ── Separator ─────────────────────────────────────────
        self._separator()

        # ── Identity config ───────────────────────────────────
        self._build_section("IDENTITY")
        self._build_identity_config()

        # ── Separator ─────────────────────────────────────────
        self._separator()

        # ── Actions ───────────────────────────────────────────
        self._build_actions()

        # ── Spacer pushes footer down ─────────────────────────
        spacer = tk.Frame(self.frame, bg=c["bg_secondary"])
        spacer.pack(fill=tk.BOTH, expand=True)

        # ── Footer ────────────────────────────────────────────
        self._build_footer()

    # ── Identity Block ────────────────────────────────────────

    def _build_identity(self):
        """Ethica's glyph and name at top of sidebar."""
        c = self.theme.colors
        f = self.theme.font

        block = tk.Frame(self.frame, bg=c["bg_secondary"], pady=16)
        block.pack(fill=tk.X)

        glyph = tk.Label(
            block,
            text="⟁Σ∿∞",
            bg=c["bg_secondary"],
            fg=c["accent_bright"],
            font=("Georgia", 14)
        )
        glyph.pack()

        name = tk.Label(
            block,
            text="Ethica",
            bg=c["bg_secondary"],
            fg=c["text_primary"],
            font=f("heading")
        )
        name.pack()

        version = tk.Label(
            block,
            text="v0.1 — walks beside",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("timestamp")
        )
        version.pack()

    # ── Model Selector ────────────────────────────────────────

    def _build_model_selector(self):
        """Dropdown to select model — Ollama or local GGUF."""
        c = self.theme.colors
        f = self.theme.font

        container = tk.Frame(self.frame, bg=c["bg_secondary"], padx=12)
        container.pack(fill=tk.X, pady=(0, 8))

        # Local GGUF models — scanned dynamically from models_dir
        from core.llama_connector import scan_models, KNOWN_MODELS
        import os
        models_dir = self.config.get("models_dir", "/srv/LLMs/models")
        scanned    = scan_models(base_dirs=[models_dir]) if os.path.exists(models_dir) else []
        # Merge scanned with KNOWN_MODELS — scanned takes priority, known as fallback
        scanned_names = {name for name, path in scanned}
        known_extras  = [(n, p) for n, p in KNOWN_MODELS.items()
                         if n not in scanned_names and os.path.exists(p)]
        all_local = scanned + known_extras
        gguf_models = [name for name, path in all_local]
        self._gguf_model_paths = {name: path for name, path in all_local}

        # Query Ollama live for installed models
        ollama_models = []
        try:
            import requests
            resp = requests.get(
                f"{self.config.get('ollama_host', 'http://localhost:11434')}/api/tags",
                timeout=3
            )
            if resp.ok:
                ollama_models = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        if not ollama_models:
            ollama_models = ["mistral", "gemma2", "deepseek-r1"]

        # Section labels via separators
        model_options = []
        if gguf_models:
            model_options += ["── Local ──"] + gguf_models
        model_options += ["── Ollama ──"] + ollama_models

        current_model = self.config.get("model", "mistral")
        # Default to first local model if available
        if gguf_models and current_model not in gguf_models + ollama_models:
            current_model = gguf_models[0]

        self._model_var = tk.StringVar(value=current_model)

        # Style the dropdown
        style = ttk.Style()
        style.configure(
            "Ethica.TCombobox",
            fieldbackground=c["bg_input"],
            background=c["bg_tertiary"],
            foreground=c["text_primary"],
            arrowcolor=c["accent_bright"],
            bordercolor=c["accent_soft"],
            lightcolor=c["bg_tertiary"],
            darkcolor=c["bg_tertiary"],
        )

        model_dropdown = ttk.Combobox(
            container,
            textvariable=self._model_var,
            values=model_options,
            state="normal",
            font=f("small"),
            style="Ethica.TCombobox"
        )
        model_dropdown.pack(fill=tk.X)
        model_dropdown.bind(
            "<<ComboboxSelected>>",
            self._on_model_selected
        )
        model_dropdown.bind("<Return>", self._on_model_selected)

        # Refresh + Apply buttons
        btn_row = tk.Frame(container, bg=c["bg_secondary"])
        btn_row.pack(fill=tk.X, pady=(4, 0))

        refresh_btn = self._make_button(
            btn_row,
            "⟳",
            lambda: self._refresh_model_list(model_dropdown)
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 2))

        apply_btn = self._make_button(
            btn_row,
            "Apply Model",
            self._on_model_selected
        )
        apply_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ── Theme Selector ────────────────────────────────────────

    def _build_theme_selector(self):
        """Theme selection buttons."""
        c = self.theme.colors
        f = self.theme.font

        container = tk.Frame(self.frame, bg=c["bg_secondary"], padx=12)
        container.pack(fill=tk.X, pady=(0, 8))

        themes = self.theme.available_themes()

        for key, name, desc in themes:
            is_active = key == self.theme.active

            btn = tk.Button(
                container,
                text=f"{'▶ ' if is_active else '   '}{name}",
                bg=c["accent_glow"] if is_active else c["bg_tertiary"],
                fg=c["text_primary"],
                font=f("small"),
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=5,
                cursor="hand2",
                anchor=tk.W,
                activebackground=c["accent_glow"],
                activeforeground=c["text_primary"],
                command=lambda k=key: self._on_theme_selected(k)
            )
            btn.pack(fill=tk.X, pady=1)

            # Hover effects
            btn.bind(
                "<Enter>",
                lambda e, b=btn: b.config(bg=c["accent_soft"])
            )
            btn.bind(
                "<Leave>",
                lambda e, b=btn, k=key: b.config(
                    bg=c["accent_glow"] if k == self.theme.active
                    else c["bg_tertiary"]
                )
            )

    # ── Identity Config ───────────────────────────────────────

    def _build_identity_config(self):
        """Your name and Ethica's name — personalisation."""
        c = self.theme.colors
        f = self.theme.font

        container = tk.Frame(self.frame, bg=c["bg_secondary"], padx=12)
        container.pack(fill=tk.X, pady=(0, 8))

        # Your name
        tk.Label(
            container,
            text="Your name",
            bg=c["bg_secondary"],
            fg=c["text_secondary"],
            font=f("small")
        ).pack(anchor=tk.W)

        self._user_name_var = tk.StringVar(
            value=self.config.get("user_name", "Friend")
        )
        user_entry = tk.Entry(
            container,
            textvariable=self._user_name_var,
            bg=c["bg_input"],
            fg=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            bd=4,
            insertbackground=c["accent_bright"]
        )
        user_entry.pack(fill=tk.X, pady=(2, 6))

        # Ethica's name
        tk.Label(
            container,
            text="Ethica's name",
            bg=c["bg_secondary"],
            fg=c["text_secondary"],
            font=f("small")
        ).pack(anchor=tk.W)

        self._ethica_name_var = tk.StringVar(
            value=self.config.get("ethica_name", "Ethica")
        )
        ethica_entry = tk.Entry(
            container,
            textvariable=self._ethica_name_var,
            bg=c["bg_input"],
            fg=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            bd=4,
            insertbackground=c["accent_bright"]
        )
        ethica_entry.pack(fill=tk.X, pady=(2, 6))

        # Save names button
        save_btn = self._make_button(
            container,
            "Save Names",
            self._save_names
        )
        save_btn.pack(fill=tk.X)

    # ── Actions ───────────────────────────────────────────────

    def _build_actions(self):
        """Action buttons — new chat etc."""
        c = self.theme.colors

        container = tk.Frame(self.frame, bg=c["bg_secondary"], padx=12)
        container.pack(fill=tk.X, pady=(0, 8))

        new_chat_btn = self._make_button(
            container,
            "✦  New Conversation",
            self._new_conversation
        )
        new_chat_btn.pack(fill=tk.X)

        mem_btn = self._make_button(
            container,
            "⟁  Memory Search",
            self._open_memory_search
        )
        mem_btn.pack(fill=tk.X, pady=(4, 0))

        tool_btn = self._make_button(
            container,
            "⟁  Tool Lister",
            self._open_tool_lister
        )
        tool_btn.pack(fill=tk.X, pady=(4, 0))

        # Chat save toggle
        toggle_row = tk.Frame(container, bg=c["bg_secondary"], pady=6)
        toggle_row.pack(fill=tk.X)
        tk.Checkbutton(
            toggle_row,
            text="  Save chat log",
            variable=self._save_chat,
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            selectcolor=c["bg_secondary"],
            activebackground=c["bg_secondary"],
            activeforeground=c.get("accent", "#9b59b6"),
            font=self.theme.font("small"),
            cursor="hand2",
            command=self._on_save_toggle
        ).pack(anchor="w")

    # ── Footer ────────────────────────────────────────────────

    def _open_memory_search(self):
        """Open the Memory Search window."""
        if not hasattr(self, '_memory_search_win'):
            self._memory_search_win = MemorySearchWindow(
                self.frame,
                self.theme,
                on_open_file=self._on_memory_file_open
            )
        self._memory_search_win.open()

    def _open_tool_lister(self):
        """Open the Tool Lister window."""
        if not hasattr(self, '_tool_lister_win'):
            self._tool_lister_win = ToolListerWindow(
                self.frame,
                self.theme,
                on_insert=self._on_tool_insert
            )
        self._tool_lister_win.open()

    def _on_tool_insert(self, syntax):
        """Insert tool syntax into chat input."""
        if hasattr(self, 'on_tool_insert') and self.on_tool_insert:
            self.on_tool_insert(syntax)

    def _on_memory_file_open(self, filepath):
        """Called when user clicks a memory result — open in canvas."""
        if hasattr(self, 'on_open_file') and self.on_open_file:
            self.on_open_file(filepath)

    def _on_save_toggle(self):
        """Called when save chat toggle changes."""
        if self.on_save_toggle:
            self.on_save_toggle(self._save_chat.get())

    def _build_footer(self):
        """Footer — free forever."""
        c = self.theme.colors
        f = self.theme.font

        sep = tk.Frame(self.frame, bg=c["separator"], height=1)
        sep.pack(fill=tk.X)

        footer = tk.Frame(self.frame, bg=c["bg_secondary"], pady=10)
        footer.pack(fill=tk.X)

        tk.Label(
            footer,
            text="Free — always.",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("timestamp")
        ).pack()

        tk.Label(
            footer,
            text="Built with ⟁ by Victory",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("timestamp")
        ).pack()

    # ── Helpers ───────────────────────────────────────────────

    def _build_section(self, title):
        """Section header label."""
        c = self.theme.colors
        f = self.theme.font

        tk.Label(
            self.frame,
            text=title,
            bg=c["bg_secondary"],
            fg=c["accent_soft"],
            font=f("small"),
            padx=12,
            pady=6,
            anchor=tk.W
        ).pack(fill=tk.X)

    def _separator(self):
        """Horizontal separator line."""
        c = self.theme.colors
        tk.Frame(
            self.frame,
            bg=c["separator"],
            height=1
        ).pack(fill=tk.X, padx=8, pady=2)

    def _make_button(self, parent, text, command):
        """Standard sidebar button."""
        c = self.theme.colors
        f = self.theme.font

        btn = tk.Button(
            parent,
            text=text,
            bg=c["button_bg"],
            fg=c["button_text"],
            font=f("button"),
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            activebackground=c["button_hover"],
            activeforeground=c["button_text"],
            command=command
        )
        btn.bind(
            "<Enter>",
            lambda e: btn.config(bg=c["button_hover"])
        )
        btn.bind(
            "<Leave>",
            lambda e: btn.config(bg=c["button_bg"])
        )
        return btn

    # ── Event Handlers ────────────────────────────────────────

    def _refresh_model_list(self, dropdown):
        """Re-scan Ollama and local GGUFs, repopulate dropdown."""
        from core.llama_connector import scan_models, KNOWN_MODELS
        import os, requests
        models_dir = self.config.get("models_dir", "/srv/LLMs/models")
        scanned = scan_models(base_dirs=[models_dir]) if os.path.exists(models_dir) else []
        scanned_names = {name for name, path in scanned}
        known_extras = [(n, p) for n, p in KNOWN_MODELS.items()
                        if n not in scanned_names and os.path.exists(p)]
        all_local = scanned + known_extras
        gguf_models = [name for name, path in all_local]
        self._gguf_model_paths = {name: path for name, path in all_local}

        ollama_models = []
        try:
            resp = requests.get(
                f"{self.config.get('ollama_host', 'http://localhost:11434')}/api/tags",
                timeout=3
            )
            if resp.ok:
                ollama_models = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        if not ollama_models:
            ollama_models = ["mistral", "gemma2", "deepseek-r1"]

        model_options = []
        if gguf_models:
            model_options += ["── Local ──"] + gguf_models
        model_options += ["── Ollama ──"] + ollama_models
        dropdown["values"] = model_options
        logging.info("[Sidebar] Refreshed — %s local, %s ollama", len(gguf_models), len(ollama_models))

    def _on_model_selected(self, event=None):
        """Fire model change callback."""
        model = self._model_var.get().strip()
        if model and model != "custom...":
            if self.on_model_change:
                self.on_model_change(model)

    def _on_theme_selected(self, theme_key):
        """Fire theme change callback."""
        if self.on_theme_change:
            self.on_theme_change(theme_key)

    def _save_names(self):
        """Save user and Ethica name to config."""
        user_name = self._user_name_var.get().strip() or "Friend"
        ethica_name = self._ethica_name_var.get().strip() or "Ethica"
        self.config.set("user_name", user_name)
        self.config.set("ethica_name", ethica_name)
        self.config.save()
        if self.on_name_save:
            self.on_name_save()

    def _new_conversation(self):
            """Start a fresh conversation."""
            if self.on_new_conversation:
                self.on_new_conversation()
    # ── Live Theme Refresh ────────────────────────────────────

    def apply_theme(self):
        """
        Repaint sidebar with current theme colors.
        Called automatically by ThemeEngine on theme switch.
        Rebuilds sidebar content in place for full refresh.
        """
        c = self.theme.colors

        # Repaint outer frame
        self.frame.config(bg=c["bg_secondary"])

        # Recursively repaint all sidebar widgets
        self._repaint_children(self.frame, c)

    def _repaint_children(self, widget, c):
        """Recursively repaint sidebar widgets."""
        try:
            wclass = widget.winfo_class()
            if wclass == "Frame":
                widget.config(bg=c["bg_secondary"])
            elif wclass == "Label":
                widget.config(bg=c["bg_secondary"])
            elif wclass == "Button":
                widget.config(
                    bg=c["bg_tertiary"],
                    fg=c["text_primary"],
                    activebackground=c["accent_glow"],
                    activeforeground=c["text_primary"]
                )
            elif wclass == "Entry":
                widget.config(
                    bg=c["bg_input"],
                    fg=c["text_primary"],
                    insertbackground=c["accent_bright"]
                )
        except Exception:
            pass

        for child in widget.winfo_children():
            self._repaint_children(child, c)
