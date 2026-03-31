"""
dashboard_ui.py — Ethica Kernel Dashboard Panel
Ethica's mission control. One view. Everything she needs.
Victory — The Architect ⟁Σ∿∞
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, font
from datetime import datetime
import json
import logging

from modules.kernel.kernel import read_all_agents, inject_task, read_agent_status

# ── Palette (matches Ethica dark theme) ───────────────────────────────────────
BG          = "#1a1333"
BG_PANEL    = "#221a3a"
BG_CARD     = "#2a1f4a"
ACCENT      = "#7c4dff"
ACCENT2     = "#b39ddb"
GREEN       = "#69ff82"
YELLOW      = "#ffe066"
RED         = "#ff5f6d"
CYAN        = "#40e0ff"
TEXT        = "#e8e0f0"
TEXT_DIM    = "#9080b0"
BORDER      = "#3d2e6e"

STATE_COLOR = {
    "IDLE":     TEXT_DIM,
    "BUILDING": GREEN,
    "SCANNING": CYAN,
    "PAUSED":   YELLOW,
    "ERROR":    RED,
    "OFFLINE":  RED,
    "RUNNING":  GREEN,
}

POLL_MS = 3000  # refresh every 3 seconds


class DashboardPanel(tk.Frame):
    """
    The Ethica Kernel Dashboard.
    Four sections: System State | Agent Ops | Quick Control | Sanctuary
    """

    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.app = app
        self._agent_frames = {}
        self._running = True

        self._build_ui()
        self._start_polling()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG, pady=8)
        header.pack(fill="x", padx=16)

        tk.Label(
            header, text="⟁Σ∿∞   ETHICA — KERNEL DASHBOARD",
            bg=BG, fg=ACCENT2,
            font=("Courier New", 11, "bold")
        ).pack(side="left")

        # ── Service indicators ────────────────────────────
        self._tm_indicator = tk.Label(
            header, text="TM ●", bg=BG, fg=TEXT_DIM,
            font=("Courier New", 9, "bold")
        )
        self._tm_indicator.pack(side="right", padx=(0, 12))
        self._fw_indicator = tk.Label(
            header, text="FW ●", bg=BG, fg=TEXT_DIM,
            font=("Courier New", 9, "bold")
        )
        self._fw_indicator.pack(side="right", padx=(0, 6))
        self._clock_label = tk.Label(
            header, text="", bg=BG, fg=TEXT_DIM,
            font=("Courier New", 9)
        )
        self._clock_label.pack(side="right")
        self._tick_clock()

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=16)

        # Main grid — 2 columns
        grid = tk.Frame(self, bg=BG)
        grid.pack(fill="both", expand=True, padx=16, pady=10)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=2)
        grid.rowconfigure(1, weight=2)
        grid.rowconfigure(2, weight=1)

        # Row 0: System State | Agent Ops
        self._system_state_frame = self._section(grid, "⬡  SYSTEM STATE", 0, 0)
        self._build_system_state(self._system_state_frame)

        self._agent_ops_frame = self._section(grid, "⬡  AGENT OPS", 0, 1)
        self._build_agent_ops(self._agent_ops_frame)

        # Row 1: Quick Control | Sanctuary
        qc_frame = self._section(grid, "⬡  QUICK CONTROL", 1, 0)
        self._build_quick_control(qc_frame)

        sanc_frame = self._section(grid, "⬡  SANCTUARY", 1, 1)
        self._build_sanctuary(sanc_frame)

        # Row 2: AnomalyDetection | Anomaly Log
        anom_frame = self._section(grid, "⬡  ANOMALY DETECTION", 2, 0)
        self._build_anomaly_detection(anom_frame)

        alog_frame = self._section(grid, "⬡  ANOMALY LOG", 2, 1)
        self._build_anomaly_log(alog_frame)

        grid.rowconfigure(2, weight=1)

        # Row 3: Memory — full width span
        mem_outer = tk.Frame(grid, bg=BORDER, padx=1, pady=1)
        mem_outer.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        grid.rowconfigure(3, weight=1)
        mem_inner = tk.Frame(mem_outer, bg=BG_PANEL)
        mem_inner.pack(fill="both", expand=True)
        tk.Label(
            mem_inner, text="⬡  MEMORY",
            bg=BG_PANEL, fg=ACCENT,
            font=("Courier New", 9, "bold"),
            pady=6, padx=10, anchor="w"
        ).pack(fill="x")
        tk.Frame(mem_inner, bg=BORDER, height=1).pack(fill="x")
        mem_body = tk.Frame(mem_inner, bg=BG_PANEL, padx=10, pady=8)
        mem_body.pack(fill="both", expand=True)
        self._build_memory(mem_body)

    def _section(self, parent, title, row, col):
        """Bordered section card."""
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        parent.rowconfigure(row, weight=1)

        inner = tk.Frame(outer, bg=BG_PANEL)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner, text=title,
            bg=BG_PANEL, fg=ACCENT,
            font=("Courier New", 9, "bold"),
            pady=6, padx=10, anchor="w"
        ).pack(fill="x")

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(inner, bg=BG_PANEL, padx=10, pady=8)
        body.pack(fill="both", expand=True)
        return body

    # ── System State ──────────────────────────────────────────────────────────

    def _build_system_state(self, parent):
        self._ss_vars = {}
        rows = [
            ("Modules Active",  "modules"),
            ("Memory Streams",  "streams"),
            ("Agents Online",   "agents"),
            ("Session Start",   "session"),
            ("Total Exchanges", "exchanges"),
        ]
        for label, key in rows:
            row = tk.Frame(parent, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"├─ {label}:", bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8), width=18, anchor="w").pack(side="left")
            var = tk.StringVar(value="—")
            self._ss_vars[key] = var
            tk.Label(row, textvariable=var, bg=BG_PANEL, fg=TEXT,
                     font=("Courier New", 8), anchor="w").pack(side="left")

        self._refresh_system_state()

    def _refresh_system_state(self):
        try:
            # Module count from app if available
            try:
                mods = len(self.app.engine.modules._modules)
                self._ss_vars["modules"].set(str(mods))
            except Exception:
                self._ss_vars["modules"].set("—")

            # Memory streams
            self._ss_vars["streams"].set("conversational | build")

            # Agents
            agents = read_all_agents()
            online = [a["agent"] for a in agents if a["state"] != "OFFLINE"]
            self._ss_vars["agents"].set(", ".join(online) if online else "None")

            # Session
            if self.app and hasattr(self.app, '_session_start'):
                self._ss_vars["session"].set(
                    self.app._session_start.strftime("%H:%M:%S"))
            else:
                self._ss_vars["session"].set(
                    datetime.now().strftime("%H:%M:%S"))

            # Exchanges
            if self.app and hasattr(self.app, 'memory_engine'):
                total = getattr(
                    self.app.memory_engine, 'total_exchanges', 136)
                self._ss_vars["exchanges"].set(str(total))
            else:
                self._ss_vars["exchanges"].set("136")

        except Exception:
            pass

    # ── Agent Ops ─────────────────────────────────────────────────────────────

    def _build_agent_ops(self, parent):
        self._agent_cards = {}
        # Scrollable frame for agent cards
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._agent_scroll_frame = tk.Frame(canvas, bg=BG)
        self._agent_scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._agent_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Bind mousewheel
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        agents = read_all_agents()
        for agent_data in agents:
            card = self._agent_card(self._agent_scroll_frame, agent_data)
            card.pack(fill="x", pady=2)
            self._agent_cards[agent_data["agent"].lower()] = card

    def _agent_card(self, parent, data):
        """Single agent status card with inject button."""
        card = tk.Frame(parent, bg=BG_CARD, padx=8, pady=6)

        name = data.get("agent", "Unknown")
        title = data.get("title", "Agent")
        state = data.get("state", "OFFLINE")
        task = data.get("current_task", "—")
        last = data.get("last_action", "—")
        progress = data.get("progress", 0)

        # Header row
        hrow = tk.Frame(card, bg=BG_CARD)
        hrow.pack(fill="x")

        tk.Label(hrow, text=name.upper(), bg=BG_CARD, fg=ACCENT2,
                 font=("Courier New", 9, "bold")).pack(side="left")
        tk.Label(hrow, text=f" — {title}", bg=BG_CARD, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(side="left")

        state_color = STATE_COLOR.get(state, TEXT_DIM)
        state_lbl = tk.Label(hrow, text=f"[{state}]", bg=BG_CARD, fg=state_color,
                             font=("Courier New", 8, "bold"))
        state_lbl.pack(side="right")
        card._state_label = state_lbl

        # Task row — hidden when IDLE
        task_var = tk.StringVar(value=f"├─ {task}")
        task_lbl = tk.Label(card, textvariable=task_var, bg=BG_CARD, fg=TEXT,
                 font=("Courier New", 8), anchor="w")
        card._task_var = task_var
        card._task_lbl = task_lbl

        # Last action — hidden when IDLE
        last_var = tk.StringVar(value=f"└─ Last: {last}")
        last_lbl = tk.Label(card, textvariable=last_var, bg=BG_CARD, fg=TEXT_DIM,
                 font=("Courier New", 7), anchor="w")
        card._last_var = last_var
        card._last_lbl = last_lbl

        # Progress bar — hidden when IDLE
        prog_frame = tk.Frame(card, bg=BG_CARD, pady=3)
        prog = ttk.Progressbar(prog_frame, length=180, maximum=100,
                               value=progress, mode="determinate")
        prog.pack(side="left")
        card._progress = prog
        card._prog_frame = prog_frame

        # Show/hide detail rows based on initial state
        if state == "IDLE":
            card._task_lbl.pack_forget()
            card._last_lbl.pack_forget()
            card._prog_frame.pack_forget()
        else:
            card._task_lbl.pack(fill="x")
            card._last_lbl.pack(fill="x")
            card._prog_frame.pack(fill="x")

        # Inject button
        inject_btn = tk.Button(
            card, text="► INJECT TASK",
            bg=ACCENT, fg="white",
            font=("Courier New", 7, "bold"),
            relief="flat", padx=6, pady=2,
            cursor="hand2",
            command=lambda n=name: self._inject_dialog(n)
        )
        inject_btn.pack(anchor="e", pady=(4, 0))

        card._agent_name = name
        return card

    def _update_agent_card(self, card, data):
        """Refresh an existing agent card with new data."""
        state = data.get("state", "OFFLINE")
        task = data.get("current_task", "—")
        last = data.get("last_action", "—")
        progress = data.get("progress", 0)
        injected = data.get("injected_task")
        acknowledged = data.get("inject_acknowledged", True)

        card._state_label.config(
            text=f"[{state}]",
            fg=STATE_COLOR.get(state, TEXT_DIM)
        )
        card._task_var.set(f"├─ {task}")
        if injected and not acknowledged:
            card._last_var.set(f"└─ ⬡ Injected: {injected}")
        else:
            card._last_var.set(f"└─ Last: {last}")
        card._progress.config(value=progress)
        # Compact when IDLE, expanded when ACTIVE
        if state == "IDLE":
            card._task_lbl.pack_forget()
            card._last_lbl.pack_forget()
            card._prog_frame.pack_forget()
        else:
            card._task_lbl.pack(fill="x")
            card._last_lbl.pack(fill="x")
            card._prog_frame.pack(fill="x")

    def _inject_dialog(self, agent_name: str):
        """Small dialog for V or Ethica to inject a task."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Inject Task → {agent_name}")
        dialog.configure(bg=BG)
        dialog.geometry("420x140")
        dialog.resizable(False, False)

        tk.Label(dialog, text=f"New directive for {agent_name.upper()}:",
                 bg=BG, fg=ACCENT2,
                 font=("Courier New", 9, "bold")).pack(padx=16, pady=(12, 4), anchor="w")

        entry = tk.Entry(dialog, bg=BG_CARD, fg=TEXT,
                         font=("Courier New", 9),
                         insertbackground=ACCENT,
                         relief="flat", width=50)
        entry.pack(padx=16, fill="x")
        entry.focus_set()

        def submit():
            task = entry.get().strip()
            if task:
                result = inject_task(agent_name, task)
                dialog.destroy()
                self._toast(result)

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="INJECT", bg=ACCENT, fg="white",
                  font=("Courier New", 8, "bold"),
                  relief="flat", padx=12, command=submit).pack(side="left", padx=6)
        tk.Button(btn_row, text="CANCEL", bg=BG_CARD, fg=TEXT_DIM,
                  font=("Courier New", 8),
                  relief="flat", padx=12, command=dialog.destroy).pack(side="left")

        entry.bind("<Return>", lambda e: submit())

    # ── Quick Control ─────────────────────────────────────────────────────────

    def _build_quick_control(self, parent):
        launches = [
            ("Canvas",   self._launch_canvas),
            ("Debug",    self._launch_debug),
            ("Project",  self._launch_project),
            ("Notes",    self._launch_notes),
        ]

        btn_row = tk.Frame(parent, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(0, 8))
        for label, cmd in launches:
            tk.Button(
                btn_row, text=label,
                bg=BG_CARD, fg=ACCENT2,
                font=("Courier New", 8, "bold"),
                relief="flat", padx=8, pady=4,
                cursor="hand2", command=cmd
            ).pack(side="left", padx=3)

        # Tool output routing
        tk.Label(parent, text="Tool Output:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(anchor="w")
        route_row = tk.Frame(parent, bg=BG_PANEL)
        route_row.pack(fill="x", pady=2)
        self._route_var = tk.StringVar(value="both")
        for val, label in [("chat", "Chat"), ("panel", "Panel"), ("both", "Both")]:
            tk.Radiobutton(
                route_row, text=label, variable=self._route_var, value=val,
                bg=BG_PANEL, fg=TEXT, selectcolor=BG_CARD,
                activebackground=BG_PANEL,
                font=("Courier New", 8)
            ).pack(side="left", padx=4)

        # Agent manager shortcut
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)
        tk.Button(
            parent, text="⬡  AGENT MANAGER",
            bg=BG_CARD, fg=CYAN,
            font=("Courier New", 8, "bold"),
            relief="flat", padx=8, pady=4,
            cursor="hand2",
            command=self._open_agent_manager
        ).pack(anchor="w")

        # ── Mnemis Vault drop zone ────────────────────────────
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)
        tk.Label(parent, text="⟁ MNEMIS VAULT",
                 bg=BG_PANEL, fg=ACCENT2,
                 font=("Courier New", 8, "bold")).pack(anchor="w")
        self._vault_drop = tk.Label(
            parent,
            text="Drop file to index memory",
            bg=BG_CARD, fg=TEXT_DIM,
            font=("Courier New", 8),
            relief="flat", pady=6, cursor="hand2"
        )
        self._vault_drop.pack(fill="x", padx=0, pady=(2, 0))
        try:
            self._vault_drop.drop_target_register("DND_Files")
            self._vault_drop.dnd_bind("<<Drop>>", self._on_vault_drop)
        except Exception:
            pass
        tk.Button(
            parent, text="Open Vault Folder",
            bg=BG_CARD, fg=TEXT_DIM,
            font=("Courier New", 7),
            relief="flat", padx=6, pady=2,
            cursor="hand2",
            command=self._launch_vault
        ).pack(anchor="w", pady=(2, 0))

    def _launch_vault(self):
        """Open the Mnemis vault folder in the file manager."""
        import subprocess
        vault = Path.home() / 'Ethica/memory/vault'
        vault.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(['xdg-open', str(vault)])
        except Exception as e:
            logging.warning('[Mnemis] vault open error: %s', e)

    def _on_vault_drop(self, event):
        """Handle file drop onto vault drop zone — index via Mnemis."""
        import shutil
        vault = Path.home() / 'Ethica/memory/vault'
        vault.mkdir(parents=True, exist_ok=True)
        filepaths = self._vault_drop.tk.splitlist(event.data)
        for src in filepaths:
            src = Path(src)
            if src.suffix.lower() in {'.txt', '.md', '.json', '.pdf'}:
                dst = vault / src.name
                shutil.copy2(str(src), str(dst))
                self._vault_drop.config(text=f"✓ {src.name} → vault")
            else:
                self._vault_drop.config(text=f"✗ {src.suffix} not supported")

    def _launch_canvas(self):
        if self.app:
            self.app.canvas.toggle()

    def _launch_debug(self):
        if self.app:
            self.app.canvas.open()
            self.app.canvas._add_debug_tab()

    def _launch_project(self):
        if self.app:
            self.app.canvas.open()
            self.app.canvas._add_project_tab()

    def _launch_notes(self):
        if self.app:
            self.app.canvas.open()
            self.app.canvas._add_tab()
            self.app._on_send("show notes")

    def _open_agent_manager(self):
        if hasattr(self, "_agent_manager_win") and self._agent_manager_win and self._agent_manager_win.winfo_exists():
            self._agent_manager_win.lift()
            return
        win = tk.Toplevel(self)
        self._agent_manager_win = win
        win.title("⬡  Agent Manager")
        win.configure(bg=BG)
        win.geometry("460x640")
        win.resizable(False, False)

        tk.Label(win, text="⬡  AGENT MANAGER", bg=BG, fg=CYAN,
                 font=("Courier New", 11, "bold")).pack(pady=(16, 4))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        scroll_frame = tk.Frame(win, bg=BG)
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=8)

        status_files = {
            "River":       os.path.expanduser("~/Ethica/status/river_status.json"),
            "Gage":        os.path.expanduser("~/Ethica/status/gage_status.json"),
            "Reka":        os.path.expanduser("~/Ethica/status/reka_status.json"),
            "Orchestrate": os.path.expanduser("~/Ethica/status/orchestrate_status.json"),
            "Debugtron":   os.path.expanduser("~/Ethica/status/debugtron_status.json"),
            "J.A.R.V.I.S.": os.path.expanduser("~/Ethica/status/jarvis_status.json"),
        }

        for agent_name, path in status_files.items():
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception:
                data = {"agent": agent_name, "title": "—", "state": "OFFLINE",
                        "current_task": "—", "last_action": "—", "updated": "—"}

            state = data.get("state", "OFFLINE")
            is_active = state == "ACTIVE"
            color = GREEN if state != "OFFLINE" else RED

            card = tk.Frame(scroll_frame, bg=BG_PANEL, pady=8, padx=10)
            card.pack(fill="x", pady=6)

            header = tk.Frame(card, bg=BG_PANEL)
            header.pack(fill="x")
            tk.Label(header, text=f"● {data.get('agent','?')} — {data.get('title','?')}",
                     bg=BG_PANEL, fg=color,
                     font=("Courier New", 9, "bold")).pack(side="left")
            tk.Label(header, text=f"[{state}]",
                     bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8)).pack(side="right")
            if is_active:
                tk.Label(header, text="⬡ RUNNING — spawn blocked",
                         bg=BG_PANEL, fg=ACCENT2,
                         font=("Courier New", 7)).pack(side="right", padx=8)

            for label, key in [("Task", "current_task"), ("Last", "last_action"), ("Updated", "updated")]:
                row = tk.Frame(card, bg=BG_PANEL)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"  ├─ {label}:", bg=BG_PANEL, fg=TEXT_DIM,
                         font=("Courier New", 7), width=10, anchor="w").pack(side="left")
                tk.Label(row, text=data.get(key, "—"), bg=BG_PANEL, fg=TEXT,
                         font=("Courier New", 7), anchor="w").pack(side="left")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)
        tk.Label(win, text="Awaiting Trinitarians:", bg=BG, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(anchor="w", padx=16)

        for _ in range(3):
            slot = tk.Frame(win, bg=BG_PANEL, pady=6, padx=10)
            slot.pack(fill="x", padx=16, pady=3)
            tk.Label(slot, text="○  [slot] — awaiting Trinitarian",
                     bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8)).pack(side="left")
            tk.Button(slot, text="+ ASSIGN", bg=BG_CARD, fg=ACCENT2,
                      font=("Courier New", 7, "bold"), relief="flat",
                      padx=6, pady=2, cursor="hand2",
                      command=lambda: self._toast("Trinitarian assignment — coming soon.")
                      ).pack(side="right")

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        tk.Button(win, text="↺  REFRESH", bg=BG_CARD, fg=CYAN,
                  font=("Courier New", 8, "bold"), relief="flat",
                  padx=8, pady=4, cursor="hand2",
                  command=lambda: [setattr(self, "_agent_manager_win", None), win.destroy(), self._open_agent_manager()]
                  ).pack(pady=(0, 12))

    # ── Sanctuary ─────────────────────────────────────────────────────────────

    def _build_anomaly_detection(self, parent):
        """AnomalyDetection card — model state and last scan summary."""
        STATUS = Path.home() / "Ethica/status/anomaly_status.json"

        # Model trained row
        r0 = tk.Frame(parent, bg=BG_PANEL)
        r0.pack(fill="x", pady=2)
        tk.Label(r0, text="├─ Model trained:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 9)).pack(side="left")
        self._anom_trained = tk.Label(r0, text="—", bg=BG_PANEL, fg=TEXT_DIM,
                                      font=("Courier New", 9, "bold"))
        self._anom_trained.pack(side="left", padx=6)

        # Last scan row
        r1 = tk.Frame(parent, bg=BG_PANEL)
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text="├─ Last scan:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 9)).pack(side="left")
        self._anom_last = tk.Label(r1, text="—", bg=BG_PANEL, fg=TEXT_DIM,
                                   font=("Courier New", 9))
        self._anom_last.pack(side="left", padx=6)

        # Total | Anomalies row
        r2 = tk.Frame(parent, bg=BG_PANEL)
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="├─ Samples:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 9)).pack(side="left")
        self._anom_total = tk.Label(r2, text="—", bg=BG_PANEL, fg=TEXT_DIM,
                                    font=("Courier New", 9))
        self._anom_total.pack(side="left", padx=6)
        tk.Label(r2, text="Anomalies:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 9)).pack(side="left", padx=(12, 0))
        self._anom_count = tk.Label(r2, text="—", bg=BG_PANEL, fg=TEXT_DIM,
                                    font=("Courier New", 9, "bold"))
        self._anom_count.pack(side="left", padx=6)

        # Store status path for poll
        self._anom_status_path = STATUS

    def _build_anomaly_log(self, parent):
        """Anomaly Log card — scrolling event list."""
        self._anom_log = tk.Text(
            parent, bg=BG_CARD, fg=TEXT_DIM,
            font=("Courier New", 8), relief="flat",
            state="disabled", wrap="word",
            height=5, padx=6, pady=4
        )
        self._anom_log.pack(fill="both", expand=True)
        self._anom_log_entries = []

    def _refresh_anomaly(self):
        """Poll anomaly_status.json and update both cards."""
        try:
            if not self._anom_status_path.exists():
                return
            data = json.loads(self._anom_status_path.read_text())
            trained = data.get("model_trained", False)
            last    = data.get("last_scan", "—")
            total   = data.get("total", "—")
            acount  = data.get("anomalies", "—")

            tcol = GREEN if trained else RED
            self._anom_trained.config(
                text="✓ Yes" if trained else "✗ No",
                fg=tcol
            )
            self._anom_last.config(text=str(last))
            self._anom_total.config(text=str(total))

            acol = RED if isinstance(acount, int) and acount > 0 else GREEN
            self._anom_count.config(text=str(acount), fg=acol)

            # Append to log if new scan
            if last != "—" and last not in self._anom_log_entries:
                self._anom_log_entries.append(last)
                entry = f"[{last}] {acount}/{total} anomalies\n"
                self._anom_log.config(state="normal")
                self._anom_log.insert("end", entry)
                self._anom_log.see("end")
                self._anom_log.config(state="disabled")
        except Exception:
            pass

    def _build_sanctuary(self, parent):
        tk.Label(parent, text="Connected Agents:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(anchor="w")

        self._sanctuary_list = tk.Frame(parent, bg=BG_PANEL)
        self._sanctuary_list.pack(fill="x", pady=4)

        self._refresh_sanctuary()

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)
        tk.Label(parent, text="Shared Context:", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(anchor="w")
        try:
            mod_count  = len(self.app.engine.modules._modules) if self.app else 0
            tool_count = sum(len(m.tools) for m in self.app.engine.modules._modules.values()) if self.app else 0
            ctx_line   = f"Ethica v0.1 — {mod_count} modules, {tool_count} tools"
        except Exception:
            ctx_line = "Ethica v0.1 — modules loading..."
        tk.Label(parent,
                 text=f"VIVARIUM — sovereign local ecosystem\n{ctx_line}",
                 bg=BG_PANEL, fg=TEXT,
                 font=("Courier New", 8), justify="left").pack(anchor="w")

    def _refresh_sanctuary(self):
        for widget in self._sanctuary_list.winfo_children():
            widget.destroy()

        agents = read_all_agents()
        for a in agents:
            state = a.get("state", "OFFLINE")
            color = GREEN if state != "OFFLINE" else RED
            indicator = "●" if state != "OFFLINE" else "○"
            row = tk.Frame(self._sanctuary_list, bg=BG_PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=indicator, bg=BG_PANEL, fg=color,
                     font=("Courier New", 10)).pack(side="left")
            tk.Label(row, text=f"  {a['agent']} — {a.get('title','Agent')}",
                     bg=BG_PANEL, fg=TEXT,
                     font=("Courier New", 8)).pack(side="left")

        # Empty slots
        for i in range(3):
            row = tk.Frame(self._sanctuary_list, bg=BG_PANEL)
            row.pack(fill="x", pady=1)
            tk.Label(row, text="○", bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 10)).pack(side="left")
            tk.Label(row, text="  [slot] — awaiting Trinitarian",
                     bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8)).pack(side="left")

    # ── Memory ────────────────────────────────────────────────────────────────

    def _build_memory(self, parent):
        self._mem_parent = parent
        self._mem_path = {
            "conversational": Path.home() / "Ethica" / "memory" / "river_conversational.json",
            "build":          Path.home() / "Ethica" / "memory" / "river_build.json",
        }

        streams = [
            ("conversational", "Conversational Stream", ACCENT2),
            ("build",          "Build Stream",          CYAN),
        ]

        for key, label, color in streams:
            row = tk.Frame(parent, bg=BG_PANEL)
            row.pack(fill="x", pady=3)

            count = self._mem_count(key)
            tk.Label(row, text=f"├─ {label}",
                     bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8), width=24, anchor="w").pack(side="left")
            tk.Label(row, text=f"[{count} entries]",
                     bg=BG_PANEL, fg=color,
                     font=("Courier New", 8)).pack(side="left", padx=6)

            tk.Button(row, text="► PEEK",
                      bg=BG_CARD, fg=color,
                      font=("Courier New", 7, "bold"),
                      relief="flat", padx=6, pady=1,
                      cursor="hand2",
                      command=lambda k=key: self._peek_stream(k)
                      ).pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)
        stats_row = tk.Frame(parent, bg=BG_PANEL)
        stats_row.pack(fill="x")

        stats = [
            ("Relationship Depth", self._get_stat("relationship_depth", "738")),
            ("Total Exchanges",    self._get_stat("total_exchanges",    "136")),
        ]
        for label, val in stats:
            tk.Label(stats_row, text=f"├─ {label}: ",
                     bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 8)).pack(side="left")
            tk.Label(stats_row, text=val,
                     bg=BG_PANEL, fg=GREEN,
                     font=("Courier New", 8, "bold")).pack(side="left", padx=(0, 16))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=6)
        tk.Label(parent, text="└─ Last build entry:",
                 bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(anchor="w")
        last = self._last_entry("build")
        tk.Label(parent, text=f"   {last}",
                 bg=BG_PANEL, fg=TEXT,
                 font=("Courier New", 8),
                 wraplength=700, justify="left").pack(anchor="w")

    def _mem_count(self, stream: str) -> int:
        path = Path.home() / "Ethica" / "memory" / f"river_{stream}.json"
        try:
            with open(path) as f:
                data = json.load(f)
            return len(data.get("entries", []))
        except Exception:
            return 0

    def _last_entry(self, stream: str) -> str:
        path = Path.home() / "Ethica" / "memory" / f"river_{stream}.json"
        try:
            with open(path) as f:
                data = json.load(f)
            entries = data.get("entries", [])
            if entries:
                last = entries[-1]
                note = last.get("note", "")
                date = last.get("date", "")
                preview = note[:80] + ("…" if len(note) > 80 else "")
                return f"[{date}] {preview}"
        except Exception:
            pass
        return "—"

    def _get_stat(self, key: str, default: str) -> str:
        try:
            if self.app and hasattr(self.app, "memory_engine"):
                val = getattr(self.app.memory_engine, key, None)
                if val is not None:
                    return str(val)
        except Exception:
            pass
        return default

    def _peek_stream(self, stream: str):
        path = Path.home() / "Ethica" / "memory" / f"river_{stream}.json"
        try:
            with open(path) as f:
                data = json.load(f)
            entries = data.get("entries", [])
        except Exception as e:
            self._toast(f"✗ Could not read {stream}: {e}")
            return

        visible = entries[-5:] if len(entries) >= 5 else entries
        visible = list(reversed(visible))

        win = tk.Toplevel(self)
        win.title(f"Memory — {stream.capitalize()} Stream")
        win.configure(bg=BG)
        win.geometry("620x400")
        win.resizable(True, True)

        tk.Label(win,
                 text=f"⬡  MEMORY — {stream.upper()} STREAM  ({len(entries)} entries, showing last 5)",
                 bg=BG, fg=ACCENT2,
                 font=("Courier New", 9, "bold"),
                 pady=8, padx=12, anchor="w").pack(fill="x")
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        frame = tk.Frame(win, bg=BG)
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame,
                       bg=BG_CARD, fg=TEXT,
                       font=("Courier New", 9),
                       relief="flat",
                       wrap="word",
                       yscrollcommand=scrollbar.set,
                       padx=10, pady=8)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)

        for entry in visible:
            date = entry.get("date", "—")
            note = entry.get("note", "")
            text.insert("end", f"[{date}]\n", "date")
            text.insert("end", f"{note}\n\n", "note")

        text.tag_config("date", foreground=ACCENT, font=("Courier New", 8, "bold"))
        text.tag_config("note", foreground=TEXT)
        text.config(state="disabled")

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(fill="x", padx=12, pady=(0, 8))

        def show_all():
            text.config(state="normal")
            text.delete("1.0", "end")
            for entry in reversed(entries):
                d = entry.get("date", "—")
                n = entry.get("note", "")
                text.insert("end", f"[{d}]\n", "date")
                text.insert("end", f"{n}\n\n", "note")
            text.tag_config("date", foreground=ACCENT, font=("Courier New", 8, "bold"))
            text.tag_config("note", foreground=TEXT)
            text.config(state="disabled")
            win.title(f"Memory — {stream.capitalize()} Stream (all {len(entries)} entries)")

        tk.Button(btn_row, text=f"SHOW ALL ({len(entries)})",
                  bg=ACCENT, fg="white",
                  font=("Courier New", 8, "bold"),
                  relief="flat", padx=10,
                  command=show_all).pack(side="left")
        tk.Button(btn_row, text="CLOSE",
                  bg=BG_CARD, fg=TEXT_DIM,
                  font=("Courier New", 8),
                  relief="flat", padx=10,
                  command=win.destroy).pack(side="left", padx=6)

    # ── Clock + Toast ─────────────────────────────────────────────────────────


    def _tick_clock(self):
        now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self._clock_label.config(text=now)
        self.after(1000, self._tick_clock)

    def _toast(self, message: str):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg=BG_CARD)
        x = self.winfo_rootx() + 40
        y = self.winfo_rooty() + 40
        toast.geometry(f"+{x}+{y}")
        tk.Label(toast, text=f"  {message}  ", bg=BG_CARD, fg=GREEN,
                 font=("Courier New", 9), pady=8).pack()
        self.after(2500, toast.destroy)

    # ── Polling ───────────────────────────────────────────────────────────────

    def _write_dashboard_context(self):
        """Write live dashboard snapshot for Ethica's context feed."""
        try:
            agents = read_all_agents()
            online = [a["agent"] for a in agents if a["state"] != "OFFLINE"]
            agent_details = []
            for a in agents:
                detail = f"{a['agent']} ({a['state']})"
                last = a.get("last_action", "")
                if last:
                    detail += f" — {last}"
                agent_details.append(detail)
            data = {
                "agents": ", ".join(online) if online else "None",
                "agent_details": agent_details,
                "modified": datetime.datetime.now().strftime("%H:%M:%S"),
            }
            ctx_path = Path.home() / "Ethica/status/dashboard_context.json"
            ctx_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _refresh_service_indicators(self):
        """Poll firewall and traffic status files, update header dots."""
        fw_file = Path.home() / "Ethica/status/firewall_status.json"
        tm_file = Path.home() / "Ethica/status/traffic_status.json"
        try:
            fw_state = json.loads(fw_file.read_text()).get("state", "IDLE") if fw_file.exists() else "IDLE"
        except Exception:
            fw_state = "IDLE"
        try:
            tm_state = json.loads(tm_file.read_text()).get("state", "IDLE") if tm_file.exists() else "IDLE"
        except Exception:
            tm_state = "IDLE"
        self._fw_indicator.config(fg=GREEN if fw_state == "ACTIVE" else TEXT_DIM)
        self._tm_indicator.config(fg=GREEN if tm_state == "ACTIVE" else TEXT_DIM)

    def _start_polling(self):
        self.after(POLL_MS, self._poll)

    def _poll(self):
        if not self._running:
            return
        try:
            self._refresh_system_state()
            self._refresh_sanctuary()
            self._refresh_anomaly()
            self._refresh_service_indicators()
            for agent_name, card in self._agent_cards.items():
                data = read_agent_status(agent_name)
                self._update_agent_card(card, data)
            self._write_dashboard_context()
        except Exception:
            pass
        self.after(POLL_MS, self._poll)

    def destroy(self):
        self._running = False
        super().destroy()
