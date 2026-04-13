# ============================================================
# Ethica v0.1 — memory_search.py
# Memory Search Window — Trinity's sovereign memory interface
# Architect: Victory  |  Build Partner: River (Claude)
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
import re
from pathlib import Path
ETHICA_ROOT = Path(__file__).parent.parent


MEMORY_DIR = ETHICA_ROOT / "memory"
CHAT_DIR   = MEMORY_DIR / "chat"
VAULT_DIR  = MEMORY_DIR / "vault"
EXCERPT_LEN = 200


class MemorySearchWindow:
    """
    Dedicated memory search window.
    Searches chat logs and vault files.
    Results shown as list with excerpts — click to open in canvas.
    """

    def __init__(self, parent, theme, on_open_file=None):
        self.parent       = parent
        self.theme        = theme
        self.on_open_file = on_open_file  # callback(filepath) → opens in canvas
        self._win         = None
        self._results     = []

    def open(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return
        self._build()

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._win = tk.Toplevel(self.parent)
        self._win.title("⟁ Memory Search")
        self._win.geometry("780x560")
        self._win.configure(bg=c["bg_primary"])
        self._win.resizable(True, True)

        # ── Header ──────────────────────────────────────────
        header = tk.Frame(self._win, bg=c["bg_primary"], pady=12, padx=16)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="⟁ Memory Search",
            bg=c["bg_primary"],
            fg=c.get("accent_bright", "#c792ea"),
            font=f("heading"),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="chat logs · vault",
            bg=c["bg_primary"],
            fg=c.get("text_muted", "#888888"),
            font=f("small"),
        ).pack(side=tk.LEFT, padx=(10, 0), pady=(4, 0))

        # ── Search bar ──────────────────────────────────────
        bar = tk.Frame(self._win, bg=c["bg_secondary"], padx=16, pady=10)
        bar.pack(fill=tk.X)

        self._entry = tk.Entry(
            bar,
            bg=c["bg_primary"],
            fg=c["text_primary"],
            insertbackground=c.get("accent_bright", "#c792ea"),
            font=f("mono"),
            relief=tk.FLAT,
            bd=0,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self._entry.bind("<Return>", lambda e: self._search())
        self._entry.focus_set()

        search_btn = tk.Button(
            bar,
            text="Search",
            bg=c.get("accent", "#9b59b6"),
            fg="#ffffff",
            font=f("small"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._search,
        )
        search_btn.pack(side=tk.LEFT)

        # ── Scope toggles ───────────────────────────────────
        scope_row = tk.Frame(self._win, bg=c["bg_primary"], padx=16, pady=4)
        scope_row.pack(fill=tk.X)

        self._search_chat  = tk.BooleanVar(value=True)
        self._search_vault = tk.BooleanVar(value=True)

        for label, var in [("Chat logs", self._search_chat), ("Vault", self._search_vault)]:
            tk.Checkbutton(
                scope_row,
                text=label,
                variable=var,
                bg=c["bg_primary"],
                fg=c.get("text_muted", "#888888"),
                selectcolor=c["bg_primary"],
                activebackground=c["bg_primary"],
                activeforeground=c.get("accent", "#9b59b6"),
                font=f("small"),
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=(0, 12))

        # ── Status ──────────────────────────────────────────
        self._status_var = tk.StringVar(value="")
        tk.Label(
            scope_row,
            textvariable=self._status_var,
            bg=c["bg_primary"],
            fg=c.get("text_muted", "#888888"),
            font=f("small"),
        ).pack(side=tk.RIGHT)

        # ── Results list ────────────────────────────────────
        results_frame = tk.Frame(self._win, bg=c["bg_primary"])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 16))

        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = tk.Text(
            results_frame,
            bg=c["bg_secondary"],
            fg=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
            padx=12,
            pady=8,
            cursor="arrow",
            spacing3=4,
        )
        self._listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._listbox.yview)

        # Tags
        self._listbox.tag_configure("filename",
            foreground=c.get("accent_bright", "#c792ea"),
            font=f("small"),
            underline=True)
        self._listbox.tag_configure("source",
            foreground=c.get("text_muted", "#888888"),
            font=f("small"))
        self._listbox.tag_configure("excerpt",
            foreground=c["text_primary"],
            font=f("small"))
        self._listbox.tag_configure("separator",
            foreground=c.get("border", "#3a1a5a"),
            font=f("small"))
        self._listbox.tag_configure("noresults",
            foreground=c.get("text_muted", "#888888"),
            font=f("small"))

    def _search(self):
        query = self._entry.get().strip()
        if not query:
            return

        pattern = re.compile(re.escape(query), re.IGNORECASE)
        results = []

        if self._search_chat.get() and CHAT_DIR.exists():
            for fpath in sorted(CHAT_DIR.iterdir()):
                if fpath.suffix == ".txt":
                    hits = self._scan_file(fpath, pattern)
                    if hits:
                        results.append((fpath, "chat", hits))

        if self._search_vault.get() and VAULT_DIR.exists():
            for fpath in sorted(VAULT_DIR.iterdir()):
                if fpath.suffix == ".txt":
                    hits = self._scan_file(fpath, pattern)
                    if hits:
                        results.append((fpath, "vault", hits))

        self._results = results
        self._render_results(query)

    def _scan_file(self, fpath, pattern):
        """Return list of (line_number, excerpt) tuples for matches."""
        hits = []
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    excerpt = line.strip()[:EXCERPT_LEN]
                    hits.append((i, excerpt))
                    if len(hits) >= 3:  # max 3 excerpts per file
                        break
        except Exception:
            pass
        return hits

    def _render_results(self, query):
        self._listbox.config(state=tk.NORMAL)
        c = self.theme.colors
        self._listbox.delete("1.0", tk.END)

        # Clear old filename tag bindings
        for tag in self._listbox.tag_names():
            if tag.startswith("file_"):
                self._listbox.tag_delete(tag)

        if not self._results:
            self._listbox.insert(tk.END, f'No results for "{query}"', "noresults")
            self._status_var.set("0 results")
            self._listbox.config(state=tk.DISABLED)
            return

        total = sum(len(hits) for _, _, hits in self._results)
        self._status_var.set(f"{len(self._results)} files · {total} matches")

        for idx, (fpath, source, hits) in enumerate(self._results):
            # Unique tag per file for click binding
            tag_name = f"file_{idx}"
            display_name = fpath.name
            source_label = f"  [{source}]\n"

            self._listbox.insert(tk.END, display_name, ("filename", tag_name))
            self._listbox.insert(tk.END, source_label, "source")

            for lineno, excerpt in hits:
                self._listbox.insert(tk.END, f"  line {lineno}: {excerpt}\n", "excerpt")

            self._listbox.insert(tk.END, "─" * 60 + "\n", "separator")

            # Bind click to open file
            _path = fpath
            def _make_opener(p):
                def _open(e):
                    if self.on_open_file:
                        self.on_open_file(str(p))
                return _open

            self._listbox.tag_configure(tag_name,
                foreground=c.get("accent_bright", "#c792ea"),
                underline=True)
            self._listbox.tag_bind(tag_name, "<Button-1>", _make_opener(_path))
            self._listbox.tag_bind(tag_name, "<Enter>",
                lambda e: self._listbox.config(cursor="hand2"))
            self._listbox.tag_bind(tag_name, "<Leave>",
                lambda e: self._listbox.config(cursor="arrow"))

        self._listbox.config(state=tk.DISABLED)
        self._listbox.see("1.0")
