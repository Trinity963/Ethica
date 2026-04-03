# ============================================================
# Ethica v0.1 — project_view.py
# Project Tab UI Renderer
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Renders a task list inside the canvas editor area.
# Replaces the text editor when tab mode is "project".
# Ethica pushes tasks, V manages them.
# ============================================================

import tkinter as tk
from tkinter import simpledialog
from core.project_engine import (
    ProjectEngine,
    STATUS_TODO, STATUS_DOING, STATUS_DONE, STATUS_BLOCKED,
    PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH,
)


class ProjectView:
    """
    Renders a project task list inside the canvas.

    Lifecycle:
        view = ProjectView(parent_frame, theme, on_change_callback)
        view.load(json_content)   # load from CanvasTab.content
        content = view.dump()     # serialize back to CanvasTab.content
        view.destroy()            # cleanup when switching tabs
    """

    def __init__(self, parent, theme, on_change=None):
        self.parent    = parent
        self.theme     = theme
        self.on_change = on_change
        self.engine    = ProjectEngine()
        self._frame    = None
        self._task_rows = {}  # task_id → row frame
        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._frame = tk.Frame(self.parent, bg=c["bg_primary"])
        self._frame.pack(fill=tk.BOTH, expand=True)

        # ── Header ────────────────────────────────────────────
        self._header = tk.Frame(self._frame, bg=c["bg_secondary"], pady=8)
        self._header.pack(fill=tk.X)

        self._title_var = tk.StringVar(value=self.engine.title)
        title_entry = tk.Entry(
            self._header,
            textvariable=self._title_var,
            bg=c["bg_secondary"],
            fg=c["accent_bright"],
            font=f("heading"),
            relief=tk.FLAT,
            insertbackground=c["accent_bright"],
            bd=0
        )
        title_entry.pack(side=tk.LEFT, padx=16, pady=4)
        title_entry.bind("<FocusOut>", self._on_title_change)
        title_entry.bind("<Return>", self._on_title_change)

        # Progress bar area
        self._progress_frame = tk.Frame(self._header, bg=c["bg_secondary"])
        self._progress_frame.pack(side=tk.RIGHT, padx=16)

        self._progress_label = tk.Label(
            self._progress_frame,
            text="0 tasks",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small")
        )
        self._progress_label.pack()

        # ── Add task bar ──────────────────────────────────────
        add_frame = tk.Frame(self._frame, bg=c["bg_tertiary"], pady=6)
        add_frame.pack(fill=tk.X)

        self._new_task_var = tk.StringVar()
        new_entry = tk.Entry(
            add_frame,
            textvariable=self._new_task_var,
            bg=c["bg_input"],
            fg=c["text_primary"],
            font=f("body"),
            relief=tk.FLAT,
            insertbackground=c["accent_bright"],
            bd=4
        )
        new_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 4))
        new_entry.bind("<Return>", self._on_add_task)

        add_btn = tk.Button(
            add_frame,
            text="+ Add",
            bg=c["button_bg"],
            fg=c["button_text"],
            font=f("small"),
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            command=self._on_add_task
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 12))

        # ── Task list (scrollable) ────────────────────────────
        list_outer = tk.Frame(self._frame, bg=c["bg_primary"])
        list_outer.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_outer, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            list_outer,
            bg=c["bg_primary"],
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._task_frame = tk.Frame(self._canvas, bg=c["bg_primary"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._task_frame, anchor=tk.NW
        )

        self._task_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mousewheel scroll
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._frame.bind("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox(tk.ALL))

    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Load / Dump ───────────────────────────────────────────

    def load(self, content):
        """Load project from CanvasTab.content JSON."""
        if content and content.strip():
            self.engine = ProjectEngine.from_json(content)
        else:
            self.engine = ProjectEngine()
        self._title_var.set(self.engine.title)
        self._refresh_tasks()
        self._refresh_progress()

    def dump(self):
        """Serialize current state to JSON string for CanvasTab.content."""
        return self.engine.to_json()

    def add_tasks_from_push(self, push_text):
        """Called by canvas when Ethica pushes [PROJECT: ...] content."""
        added = self.engine.add_tasks_from_push(push_text)
        self._refresh_tasks()
        self._refresh_progress()
        if self.on_change:
            self.on_change()
        return added

    # ── Render ────────────────────────────────────────────────

    def _refresh_tasks(self):
        """Re-render all task rows."""
        c = self.theme.colors
        f = self.theme.font

        # Clear existing rows
        for widget in self._task_frame.winfo_children():
            widget.destroy()
        self._task_rows.clear()

        if not self.engine.tasks:
            tk.Label(
                self._task_frame,
                text="No tasks yet.\nAsk Ethica to add some, or type above.",
                bg=c["bg_primary"],
                fg=c["text_muted"],
                font=f("body"),
                justify=tk.CENTER,
                pady=40
            ).pack()
            return

        for task in self.engine.tasks:
            self._render_task_row(task)

    def _render_task_row(self, task):
        """Render a single task row."""
        c = self.theme.colors
        f = self.theme.font

        is_done = task.status == STATUS_DONE

        row_bg = c["bg_secondary"] if not is_done else c["bg_tertiary"]
        text_color = c["text_muted"] if is_done else c["text_primary"]

        row = tk.Frame(
            self._task_frame,
            bg=row_bg,
            pady=6,
            padx=8,
            relief=tk.FLAT
        )
        row.pack(fill=tk.X, pady=1, padx=4)
        self._task_rows[task.id] = row

        # ── Status button ──────────────────────────────────
        status_btn = tk.Button(
            row,
            text=task.status_icon,
            bg=row_bg,
            fg=self._status_color(task.status, c),
            font=f("body_bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=lambda t=task: self._cycle_status(t)
        )
        status_btn.pack(side=tk.LEFT)

        # ── Priority button ────────────────────────────────
        pri_btn = tk.Button(
            row,
            text=task.priority_icon,
            bg=row_bg,
            fg=self._priority_color(task.priority, c),
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=2,
            command=lambda t=task: self._cycle_priority(t)
        )
        pri_btn.pack(side=tk.LEFT)

        # ── Task text ──────────────────────────────────────
        task_label = tk.Label(
            row,
            text=task.text,
            bg=row_bg,
            fg=text_color,
            font=f("body"),
            anchor=tk.W,
            wraplength=500,
            justify=tk.LEFT
        )
        task_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # Strike through done tasks visually
        if is_done:
            task_label.config(font=f("body"))

        # ── Actions ───────────────────────────────────────
        actions = tk.Frame(row, bg=row_bg)
        actions.pack(side=tk.RIGHT)

        # Note button
        note_indicator = "📝" if task.note else "·"
        tk.Button(
            actions,
            text=note_indicator,
            bg=row_bg,
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=2,
            command=lambda t=task: self._edit_note(t)
        ).pack(side=tk.LEFT)

        # Delete button
        tk.Button(
            actions,
            text="✕",
            bg=row_bg,
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=lambda t=task: self._delete_task(t)
        ).pack(side=tk.LEFT)

        # Show note if present
        if task.note:
            note_row = tk.Frame(self._task_frame, bg=c["bg_primary"], padx=40)
            note_row.pack(fill=tk.X, padx=4)
            tk.Label(
                note_row,
                text=f"  ↳ {task.note}",
                bg=c["bg_primary"],
                fg=c["text_muted"],
                font=f("small"),
                anchor=tk.W,
                wraplength=520,
                justify=tk.LEFT
            ).pack(fill=tk.X)

    def _status_color(self, status, c):
        return {
            STATUS_TODO:    c["text_muted"],
            STATUS_DOING:   c["accent_bright"],
            STATUS_DONE:    c.get("status_online", "#4caf50"),
            STATUS_BLOCKED: "#e57373",
        }.get(status, c["text_muted"])

    def _priority_color(self, priority, c):
        return {
            PRIORITY_HIGH:   c["accent_bright"],
            PRIORITY_NORMAL: c["text_muted"],
            PRIORITY_LOW:    c["bg_tertiary"],
        }.get(priority, c["text_muted"])

    def _refresh_progress(self):
        stats = self.engine.stats
        if stats["total"] == 0:
            self._progress_label.config(text="No tasks")
        else:
            self._progress_label.config(
                text=f"{stats['done']}/{stats['total']} done  ·  {stats['percent']}%"
            )

    # ── Interactions ──────────────────────────────────────────

    def _on_add_task(self, event=None):
        text = self._new_task_var.get().strip()
        if not text:
            return
        self.engine.add_task(text)
        self._new_task_var.set("")
        self._refresh_tasks()
        self._refresh_progress()
        if self.on_change:
            self.on_change()

    def _cycle_status(self, task):
        task.cycle_status()
        self._refresh_tasks()
        self._refresh_progress()
        if self.on_change:
            self.on_change()

    def _cycle_priority(self, task):
        task.cycle_priority()
        self._refresh_tasks()
        if self.on_change:
            self.on_change()

    def _delete_task(self, task):
        self.engine.remove_task(task.id)
        self._refresh_tasks()
        self._refresh_progress()
        if self.on_change:
            self.on_change()

    def _edit_note(self, task):
        note = simpledialog.askstring(
            "Task Note",
            f"Note for: {task.text[:50]}",
            initialvalue=task.note,
            parent=self._frame
        )
        if note is not None:
            task.note = note.strip()
            self._refresh_tasks()
            if self.on_change:
                self.on_change()

    def _on_title_change(self, event=None):
        self.engine.title = self._title_var.get().strip() or "Project"
        if self.on_change:
            self.on_change()

    # ── Cleanup ───────────────────────────────────────────────

    def destroy(self):
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
