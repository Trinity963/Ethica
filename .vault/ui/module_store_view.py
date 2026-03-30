# ============================================================
# Ethica v0.1 — module_store_view.py
# Module Store — canvas view showing installed modules
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk


class ModuleStoreView:
    def __init__(self, parent, theme, config, module_registry, on_change=None):
        self.parent   = parent
        self.theme    = theme
        self.config   = config
        self.modules  = module_registry
        self.on_change = on_change
        self._frame   = None
        self._cards   = {}
        self._build()
        self.refresh()

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._frame = tk.Frame(self.parent, bg=c["bg_primary"])
        self._frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(self._frame, bg=c["bg_primary"], pady=12, padx=16)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="⟁ Module Store",
            bg=c["bg_primary"],
            fg=c["text_primary"],
            font=f("heading"),
        ).pack(side=tk.LEFT)

        tk.Button(
            header,
            text="↺ Reload All",
            bg=c.get("button_bg", "#4a1a6a"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=10, pady=4,
            cursor="hand2",
            command=self._reload_all
        ).pack(side=tk.RIGHT)

        tk.Button(
            header,
            text="⟁ Create Module",
            bg=c.get("accent", "#9b59b6"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=10, pady=4,
            cursor="hand2",
            command=self._create_module
        ).pack(side=tk.RIGHT, padx=(0, 8))

        tk.Button(
            header,
            text="+ Install from Path",
            bg=c.get("button_bg", "#4a1a6a"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=10, pady=4,
            cursor="hand2",
            command=self._show_install_bar
        ).pack(side=tk.RIGHT, padx=(0, 8))

        tk.Frame(self._frame, bg=c.get("border", "#3a1a5a"), height=1).pack(fill=tk.X, padx=16)

        # Install bar — hidden by default
        self._install_bar = tk.Frame(self._frame, bg=c.get("bg_secondary", "#1a0a2e"), padx=16, pady=8)
        self._path_var = tk.StringVar()
        tk.Label(
            self._install_bar,
            text="Module path:",
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_muted"],
            font=f("small")
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Entry(
            self._install_bar,
            textvariable=self._path_var,
            bg=c.get("bg_primary", "#0d0d1a"),
            fg=c["text_primary"],
            insertbackground=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            width=50
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            self._install_bar,
            text="Browse",
            bg=c.get("button_bg", "#4a1a6a"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=8, pady=2,
            cursor="hand2",
            command=self._browse_path
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(
            self._install_bar,
            text="Install",
            bg=c.get("accent", "#9b59b6"),
            fg=c.get("button_text", "#ffffff"),
            font=f("small"),
            relief=tk.FLAT,
            padx=8, pady=2,
            cursor="hand2",
            command=self._install_module
        ).pack(side=tk.LEFT)
        self._install_status = tk.Label(
            self._install_bar,
            text="",
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c.get("accent", "#9b59b6"),
            font=f("small")
        )
        self._install_status.pack(side=tk.LEFT, padx=(12, 0))

        container = tk.Frame(self._frame, bg=c["bg_primary"])
        container.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(container, bg=c["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=c["bg_primary"])
        self._canvas_window = self._canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>",     self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>",    self._on_mousewheel)
        self._canvas.bind("<Button-4>",      self._on_mousewheel)
        self._canvas.bind("<Button-5>",      self._on_mousewheel)

    def refresh(self):
        c = self.theme.colors
        f = self.theme.font

        for w in self._list_frame.winfo_children():
            w.destroy()
        self._cards.clear()

        modules = self.modules.list_modules() if self.modules else []

        if not modules:
            tk.Label(
                self._list_frame,
                text="No modules loaded.",
                bg=c["bg_primary"],
                fg=c["text_muted"],
                font=f("body"),
                pady=24
            ).pack()
            return

        for mod in modules:
            self._build_card(mod)

        tool_count = sum(m.get("tool_count", 0) for m in modules)
        tk.Label(
            self._list_frame,
            text=f"{len(modules)} module(s) — {tool_count} tool(s) available",
            bg=c["bg_primary"],
            fg=c["text_muted"],
            font=f("small"),
            pady=12
        ).pack()

    def _build_card(self, mod):
        c = self.theme.colors
        f = self.theme.font

        name        = mod.get("name", "Unknown")
        version     = mod.get("version", "?")
        description = mod.get("description", "")
        tools       = mod.get("tools", [])
        enabled     = mod.get("enabled", True)
        author      = mod.get("author", "")

        card = tk.Frame(
            self._list_frame,
            bg=c.get("bg_secondary", "#1a0a2e"),
            padx=16, pady=12,
        )
        card.pack(fill=tk.X, padx=16, pady=(8, 0))

        header_row = tk.Frame(card, bg=c.get("bg_secondary", "#1a0a2e"))
        header_row.pack(fill=tk.X)

        dot_color = c.get("accent", "#9b59b6") if enabled else c.get("text_muted", "#888")
        tk.Label(header_row, text="●", bg=c.get("bg_secondary", "#1a0a2e"),
                 fg=dot_color, font=f("small")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(header_row, text=f"{name}  v{version}",
                 bg=c.get("bg_secondary", "#1a0a2e"),
                 fg=c["text_primary"], font=f("heading")).pack(side=tk.LEFT)

        if author:
            tk.Label(header_row, text=f"by {author}",
                     bg=c.get("bg_secondary", "#1a0a2e"),
                     fg=c["text_muted"], font=f("small"), padx=8).pack(side=tk.LEFT)

        enabled_var = tk.BooleanVar(value=enabled)
        tk.Checkbutton(
            header_row,
            text="Enabled",
            variable=enabled_var,
            bg=c.get("bg_secondary", "#1a0a2e"),
            fg=c["text_muted"],
            selectcolor=c.get("bg_secondary", "#1a0a2e"),
            activebackground=c.get("bg_secondary", "#1a0a2e"),
            font=f("small"),
            cursor="hand2",
            command=lambda n=name, v=enabled_var: self._toggle_module(n, v)
        ).pack(side=tk.RIGHT)

        if description:
            tk.Label(card, text=description,
                     bg=c.get("bg_secondary", "#1a0a2e"),
                     fg=c["text_muted"], font=f("small"),
                     wraplength=500, justify=tk.LEFT, pady=4).pack(anchor="w")

        if tools:
            tools_frame = tk.Frame(card, bg=c.get("bg_secondary", "#1a0a2e"), pady=4)
            tools_frame.pack(fill=tk.X)
            tk.Label(tools_frame, text="Tools:",
                     bg=c.get("bg_secondary", "#1a0a2e"),
                     fg=c["text_muted"], font=f("small")).pack(anchor="w")
            for tool in tools:
                tk.Label(tools_frame, text=f"  ⟁ {tool}",
                         bg=c.get("bg_secondary", "#1a0a2e"),
                         fg=c.get("accent_soft", "#6b3fa0"),
                         font=f("small")).pack(anchor="w", padx=8)

        tk.Frame(card, bg=c.get("border", "#3a1a5a"), height=1).pack(fill=tk.X, pady=(8, 0))
        self._cards[name] = card

    def _toggle_module(self, name, var):
        if self.modules:
            self.modules.set_enabled(name, var.get())
        self.refresh()

    def _reload_all(self):
        if self.modules:
            self.modules.reload()
        self.refresh()

    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_install_bar(self):
        """Toggle the install bar visibility."""
        if self._install_bar.winfo_ismapped():
            self._install_bar.pack_forget()
        else:
            self._install_bar.pack(fill=tk.X, after=self._frame.winfo_children()[1])

    def _browse_path(self):
        """Open file dialog to pick a module folder."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Module Folder")
        if path:
            self._path_var.set(path)

    def _install_module(self):
        """Hot-load a module from the path in the entry field."""
        import shutil, os
        path = self._path_var.get().strip()
        if not path:
            self._install_status.config(text="⚠ Enter a path first")
            return
        if not os.path.isdir(path):
            self._install_status.config(text=f"⚠ Not a directory: {path}")
            return
        manifest = os.path.join(path, "manifest.json")
        if not os.path.exists(manifest):
            self._install_status.config(text="⚠ No manifest.json found")
            return
        # Copy to modules dir if not already there
        from pathlib import Path
        modules_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "modules"
        dest = modules_dir / os.path.basename(path)
        if not dest.exists():
            try:
                shutil.copytree(path, dest)
            except Exception as e:
                self._install_status.config(text=f"⚠ Copy failed: {e}")
                return
        # Hot-load
        result = self.modules.register_module(str(dest))
        self._install_status.config(text=result.replace("[ModuleRegistry] ", ""))
        self._path_var.set("")
        self.refresh()
        if self.on_change:
            self.on_change()

    def _create_module(self):
        """Generate a new module boilerplate and push to canvas."""
        import tkinter.simpledialog as sd
        name = sd.askstring("Create Module", "Module name (e.g. MyTool):")
        if not name:
            return
        name = name.strip().replace(" ", "_")
        boilerplate_py = f"""# ============================================================
# Ethica Module — {name.lower()}.py
# {name}
# Architect: Victory  |  Build Partner: Ethica
# ⟁Σ∿∞
# ============================================================

def {name.lower()}_run(input_str):
    '''\n    Tool: {name.lower()}_run\n    Input: your input here\n    Returns: result string\n    '''
    data = input_str.strip()
    if not data:
        return "{name} — no input provided."
    # TODO: implement tool logic here
    return f"{name} — received: {{data}}"


# ── Module registry interface ─────────────────────────────────

TOOLS = {{
    "{name.lower()}_run": {name.lower()}_run,
}}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[{name}] Unknown tool: {{tool_name}}"
"""
        boilerplate_json = f"""{{
  "name": "{name}",
  "version": "1.0",
  "description": "{name} — created inside Ethica",
  "author": "Victory",
  "autonomous": false,
  "autonomous_triggers": [],
  "tools": [
    {{
      "name": "{name.lower()}_run",
      "description": "Main tool for {name}",
      "syntax": "[TOOL:{name.lower()}_run: input]",
      "autonomous": false,
      "example": "[TOOL:{name.lower()}_run: test]"
    }}
  ]
}}"""
        # Push both files to canvas
        if self.on_change:
            self.on_change("create_module", name, boilerplate_py, boilerplate_json)

    def destroy(self):
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
