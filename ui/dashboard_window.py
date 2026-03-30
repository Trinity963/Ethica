# ============================================================
# Ethica v0.1 — dashboard_window.py
# Kernel Dashboard — Floating Toplevel
# Architect: Victory  |  Build Partner: River
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
from modules.kernel.dashboard_ui import DashboardPanel

DEFAULT_W = 1280
DEFAULT_H = 820
MIN_W     = 900
MIN_H     = 600
TITLE     = "⟁ Ethica — Kernel Dashboard"


class DashboardWindow:
    """
    Floating Toplevel for the Kernel Dashboard.
    Same open/close/toggle pattern as CanvasWindow.
    Ethica can open it programmatically. V can call 'dashboard'.
    """

    def __init__(self, parent, theme, config, app=None):
        self.parent = parent
        self.theme  = theme
        self.config = config
        self.app    = app

        self._window  = None
        self._panel   = None
        self._is_open = False

    # ── Public API ────────────────────────────────────────────

    def open(self):
        """Open the dashboard. Creates if not exists, lifts if already open."""
        if self._window and self._window.winfo_exists():
            self._window.lift()
            self._window.focus_force()
            return

        self._build_window()
        self._is_open = True

    def close(self):
        """Close the dashboard window."""
        if self._window:
            self._window.destroy()
            self._window = None
        if self._panel:
            self._panel = None
        self._is_open = False

    def toggle(self):
        """Toggle dashboard open/closed."""
        if self._is_open and self._window and self._window.winfo_exists():
            self.close()
        else:
            self.open()

    def is_open(self):
        return self._is_open and self._window and self._window.winfo_exists()

    # ── Build ─────────────────────────────────────────────────

    def _build_window(self):
        c = self.theme.colors

        geo = self.config.get(
            "dashboard_geometry",
            f"{DEFAULT_W}x{DEFAULT_H}+120+80"
        )

        self._window = tk.Toplevel(self.parent)
        self._window.title(TITLE)
        self._window.geometry(geo)
        self._window.minsize(MIN_W, MIN_H)
        self._window.resizable(True, True)
        self._window.configure(bg=c.get("bg_primary", "#1a1333"))

        self._window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._window.bind("<Configure>", self._on_configure)

        # Dashboard panel fills the window
        self._panel = DashboardPanel(self._window, app=self.app)
        self._panel.pack(fill=tk.BOTH, expand=True)

    def _on_close(self):
        self._save_geometry()
        self.close()

    def _on_configure(self, event):
        self._save_geometry()

    def _save_geometry(self):
        if self._window and self._window.winfo_exists():
            try:
                self.config["dashboard_geometry"] = self._window.geometry()
            except Exception:
                pass
