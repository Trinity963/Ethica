# ============================================================
# Ethica v0.1 — main.py
# Application Entry Point
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
try:
    from tkinterdnd2 import TkinterDnD
    _DND = True
except ImportError:
    _DND = False
try:
    from tkinterdnd2 import TkinterDnD
    _DND = True
except ImportError:
    _DND = False
import sys
import os

# ── Path Setup (portable — no absolute paths) ─────────────────
# Ensures all imports work regardless of where Ethica is installed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Imports ───────────────────────────────────────────────────
from ui.theme import theme
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from modules.crash_reporter.crash_reporter_tool import install_excepthook, check_crash_log
from modules.ethica_guard.ethica_guard import startup_check


# ── Boot Sequence ─────────────────────────────────────────────

def boot():
    """
    Ethica boot sequence.
    1. Load user config (theme preference, model selection, etc.)
    2. Apply saved theme
    3. Launch main window
    """

    # Load user config — creates default if none exists
    config = ConfigManager()

    # Apply saved theme preference
    saved_theme = config.get("theme", "purple")
    theme.switch(saved_theme)

    # Init Tkinter root
    root = TkinterDnD.Tk() if _DND else tk.Tk()
    root.title("Ethica")
    root.geometry("900x680")
    root.minsize(700, 500)

    # Apply window background immediately — no white flash on load
    root.configure(bg=theme.get("bg_primary"))

    # Center window on screen
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = 900
    win_h = 680
    x = (screen_w // 2) - (win_w // 2)
    y = (screen_h // 2) - (win_h // 2)
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # Remove default title bar border (clean look)
    # root.overrideredirect(True)  # Uncomment for frameless — Phase 2

    # Launch main window — passes root, theme, config
    app = MainWindow(root, theme, config)

    # Install global crash handler — before mainloop
    install_excepthook()

    # Check for crash log from previous session
    check_crash_log(root)
    # Integrity check — warn if architecture tampered
    _integrity_warning = startup_check()
    if _integrity_warning:
        import tkinter.messagebox as mb
        mb.showwarning(
            '⚠ Ethica Integrity Warning',
            f'{_integrity_warning}\n\n'
            'If you did not make these changes, Ethica\'s architecture may have been tampered with.\n\n'
            'Continuing may result in loss of all learned memory, tool usage history, and retained context.\n'
            'A fresh install may be required to restore integrity.\n\n'
            'Proceeding anyway.'
        )

    # Handle clean close
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, config, app))

    # Start event loop
    root.mainloop()


def on_close(root, config, app=None):
    """
    Clean shutdown.
    Save any unsaved config before exit.
    """
    config.save()
    if app is not None:
        try:
            app._on_close()
            return  # _on_close calls root.destroy() itself
        except Exception:
            pass
    root.destroy()


# ── Entry Point ───────────────────────────────────────────────

if __name__ == "__main__":
    boot()
