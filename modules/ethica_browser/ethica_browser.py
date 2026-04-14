# ── EthicaBrowser — The Browser ─────────────────────────────
# Sovereign embedded browser via pywebview.
# Cross-platform: WebKit (Mac), WebKitGTK (Linux), EdgeHTML (Windows).
# Slot 8 — replaces Nyxt.
# Runs as subprocess — pywebview requires main thread ownership.

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

SEARCH_ENGINE = "https://duckduckgo.com/?q="
LAUNCHER = Path(__file__).parent / "ethica_browser_launcher.py"

_proc = None


def _is_running() -> bool:
    global _proc
    if _proc and _proc.poll() is None:
        return True
    _proc = None
    return False


def browser_open(args: str = "") -> str:
    global _proc
    url = args.strip()
    if not url:
        return "Usage: browser open <url>"

    if not LAUNCHER.exists():
        return f"EthicaBrowser — launcher not found: {LAUNCHER}"

    if not url.startswith("http"):
        url = "https://" + url

    if _is_running():
        _proc.terminate()
        _proc = None

    try:
        _proc = subprocess.Popen(
            [sys.executable, str(LAUNCHER), url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"EthicaBrowser: opening {url} (PID {_proc.pid})")
        return f"EthicaBrowser — opening: {url}"
    except Exception as e:
        return f"EthicaBrowser — failed to launch: {e}"


def browser_search(args: str = "") -> str:
    query = args.strip()
    if not query:
        return "Usage: browser search <query>"
    url = SEARCH_ENGINE + query.replace(" ", "+")
    return browser_open(url)


def browser_status(args: str = "") -> str:
    if _is_running():
        return f"EthicaBrowser — RUNNING (PID {_proc.pid})"
    return "EthicaBrowser — not running. Use: browser open <url>"


def browser_close(args: str = "") -> str:
    global _proc
    if not _is_running():
        return "EthicaBrowser — not running."
    try:
        _proc.terminate()
        _proc = None
        return "EthicaBrowser — closed."
    except Exception as e:
        return f"EthicaBrowser — close failed: {e}"
