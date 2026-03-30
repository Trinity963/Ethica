# ============================================================
# Ethica v0.1 — tool_lister.py
# Tool Lister — Browse and launch all Ethica tools
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
from pathlib import Path
import json


class ToolListerWindow:
    """
    Popup window showing all Ethica tools grouped by module.
    Filter box at top. Click any tool to insert its syntax into chat.
    """

    def __init__(self, parent, theme, on_insert=None):
        self.parent    = parent
        self.theme     = theme
        self.on_insert = on_insert  # callback(syntax_str) → inserts into chat input
        self._win      = None
        self._all_tools = []  # flat list of (module_name, tool_name, description, syntax, example)

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return
        self._load_tools()
        self._build()

    def _load_tools(self):
        """Walk modules/ and read manifests."""
        self._all_tools = []
        modules_dir = Path.home() / "Ethica/modules"
        if not modules_dir.exists():
            return
        for module_dir in sorted(modules_dir.iterdir()):
            manifest_path = module_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                module_name = manifest.get("name", module_dir.name)
                tools = manifest.get("tools", [])
                for t in tools:
                    name    = t.get("name", "")
                    desc    = t.get("description", "")
                    syntax  = t.get("syntax", f"[TOOL:{name}: input]")
                    example = t.get("example", "")
                    if name:
                        self._all_tools.append((module_name, name, desc, syntax, example))
            except Exception:
                continue

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._win = tk.Toplevel(self.parent)
        self._win.title("⟁ Tool Lister")
        self._win.geometry("820x600")
        self._win.configure(bg=c["bg_primary"])
        self._win.resizable(True, True)

        # ── Header ──────────────────────────────────────────
        header = tk.Frame(self._win, bg=c["bg_primary"], pady=12, padx=16)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="⟁ Tool Lister",
            bg=c["bg_primary"],
            fg=c.get("accent_bright", "#c792ea"),
            font=f("heading"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="click any tool to insert into chat",
            bg=c["bg_primary"],
            fg=c.get("text_muted", "#888888"),
            font=f("small"),
        ).pack(side=tk.LEFT, padx=(10, 0), pady=(4, 0))

        # ── Filter bar ──────────────────────────────────────
        bar = tk.Frame(self._win, bg=c["bg_secondary"], padx=16, pady=10)
        bar.pack(fill=tk.X)

        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())

        self._entry = tk.Entry(
            bar,
            textvariable=self._filter_var,
            bg=c["bg_primary"],
            fg=c["text_primary"],
            insertbackground=c.get("accent_bright", "#c792ea"),
            font=f("mono"),
            relief=tk.FLAT,
            bd=0,
        )
        self._entry.pack(fill=tk.X, ipady=6)
        self._entry.insert(0, "")
        self._entry.focus_set()

        self._placeholder = tk.Label(
            bar,
            text="filter tools...",
            bg=c["bg_secondary"],
            fg=c.get("text_muted", "#666666"),
            font=f("small"),
        )
        self._placeholder.place(in_=self._entry, x=4, y=4)

        # ── Scrollable results ───────────────────────────────
        body = tk.Frame(self._win, bg=c["bg_primary"])
        body.pack(fill=tk.BOTH, expand=True, padx=0, pady=(4, 0))

        scrollbar = tk.Scrollbar(body, orient=tk.VERTICAL,
                                  bg=c["bg_secondary"], troughcolor=c["bg_primary"],
                                  relief=tk.FLAT, bd=0, width=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            body,
            bg=c["bg_primary"],
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._inner = tk.Frame(self._canvas, bg=c["bg_primary"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )
        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas.bind("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

        # ── Footer ───────────────────────────────────────────
        footer = tk.Frame(self._win, bg=c["bg_secondary"], pady=8, padx=16)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        self._count_label = tk.Label(
            footer,
            text=f"{len(self._all_tools)} tools across all modules",
            bg=c["bg_secondary"],
            fg=c.get("text_muted", "#888888"),
            font=f("small"),
        )
        self._count_label.pack(side=tk.LEFT)

        self._apply_filter()

    def _on_inner_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _apply_filter(self):
        """Rebuild tool list based on current filter text."""
        c = self.theme.colors
        f = self.theme.font
        query = self._filter_var.get().lower().strip() if hasattr(self, "_filter_var") else ""
        # Hide placeholder when typing, show when empty
        if hasattr(self, "_placeholder"):
            if query:
                self._placeholder.place_forget()
            else:
                self._placeholder.place(in_=self._entry, x=4, y=4)

        for widget in self._inner.winfo_children():
            widget.destroy()

        # Group by module
        modules = {}
        for (mod, name, desc, syntax, example) in self._all_tools:
            if query and query not in mod.lower() and query not in name.lower() and query not in desc.lower():
                continue
            if mod not in modules:
                modules[mod] = []
            modules[mod].append((name, desc, syntax, example))

        visible = sum(len(v) for v in modules.values())

        for mod_name, tools in modules.items():
            # Module header
            mod_hdr = tk.Frame(self._inner, bg=c.get("bg_secondary", "#1a0a2e"), pady=4, padx=12)
            mod_hdr.pack(fill=tk.X, pady=(8, 0))
            tk.Label(
                mod_hdr,
                text=f"  {mod_name}",
                bg=c.get("bg_secondary", "#1a0a2e"),
                fg=c.get("accent_bright", "#c792ea"),
                font=f("bold") if hasattr(f, "__call__") else ("TkDefaultFont", 10, "bold"),
                anchor="w",
            ).pack(fill=tk.X)

            for (name, desc, syntax, example) in tools:
                self._make_tool_row(self._inner, mod_name, name, desc, syntax, example)

        if hasattr(self, "_count_label"):
            self._count_label.config(text=f"{visible} tool(s) shown")

    def _make_tool_row(self, parent, mod_name, name, desc, syntax, example):
        """Build one clickable tool row."""
        c = self.theme.colors
        f = self.theme.font

        row = tk.Frame(parent, bg=c["bg_primary"], padx=16, pady=6, cursor="hand2")
        row.pack(fill=tk.X)

        # Separator line
        sep = tk.Frame(row, bg=c.get("border", "#2a1a4a"), height=1)
        sep.pack(fill=tk.X, pady=(0, 6))

        # Tool name
        name_lbl = tk.Label(
            row,
            text=f"  {name}",
            bg=c["bg_primary"],
            fg=c.get("accent", "#9b59b6"),
            font=f("mono"),
            anchor="w",
            cursor="hand2",
        )
        name_lbl.pack(fill=tk.X)

        # Description
        if desc:
            desc_lbl = tk.Label(
                row,
                text=f"    {desc}",
                bg=c["bg_primary"],
                fg=c.get("text_muted", "#888888"),
                font=f("small"),
                anchor="w",
                wraplength=680,
                justify=tk.LEFT,
                cursor="hand2",
            )
            desc_lbl.pack(fill=tk.X)

        # Syntax
        syntax_lbl = tk.Label(
            row,
            text=f"    {syntax}",
            bg=c["bg_primary"],
            fg=c.get("text_secondary", "#aaaaaa"),
            font=f("mono"),
            anchor="w",
            cursor="hand2",
        )
        syntax_lbl.pack(fill=tk.X)

        # Hover + click binding
        def _on_enter(e, r=row):
            r.config(bg=c.get("bg_secondary", "#1a0a2e"))
            for child in r.winfo_children():
                try:
                    child.config(bg=c.get("bg_secondary", "#1a0a2e"))
                except Exception:
                    pass

        def _on_leave(e, r=row):
            r.config(bg=c["bg_primary"])
            for child in r.winfo_children():
                try:
                    child.config(bg=c["bg_primary"])
                except Exception:
                    pass

        def _on_click(e, s=syntax):
            if self.on_insert:
                self.on_insert(s)

        for widget in [row] + row.winfo_children():
            widget.bind("<Enter>", _on_enter)
            widget.bind("<Leave>", _on_leave)
            widget.bind("<Button-1>", _on_click)
