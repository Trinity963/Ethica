# ── EthicaBrowser — The Browser ─────────────────────────────
# Sovereign embedded browser via pywebview.
# Cross-platform: WebKit (Mac), WebKitGTK (Linux), EdgeHTML (Windows).
# Slot 8 — replaces Nyxt.

import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_window = None
_thread = None
_current_url = ""
SEARCH_ENGINE = "https://duckduckgo.com/?q="


def _ensure_webview():
    try:
        import webview
        return webview
    except ImportError:
        return None


def _launch_window(url: str):
    global _window, _current_url
    wv = _ensure_webview()
    if not wv:
        return
    _current_url = url
    _window = wv.create_window(
        "EthicaBrowser — Sovereign",
        url,
        width=1200,
        height=800,
        resizable=True,
    )
    wv.start()
    _window = None
    _current_url = ""


def browser_open(args: str = "") -> str:
    global _thread
    url = args.strip()
    if not url:
        return "Usage: browser open <url>"

    wv = _ensure_webview()
    if not wv:
        return (
            "EthicaBrowser — pywebview not installed.\n"
            "  Run: pip install pywebview"
        )

    if not url.startswith("http"):
        url = "https://" + url

    if _thread and _thread.is_alive():
        if _window:
            try:
                _window.load_url(url)
                return f"EthicaBrowser — navigated to: {url}"
            except Exception as e:
                return f"EthicaBrowser — navigation failed: {e}"
        return "EthicaBrowser — window busy. Use browser close first."

    _thread = threading.Thread(target=_launch_window, args=(url,), daemon=True)
    _thread.start()
    logger.info(f"EthicaBrowser: opening {url}")
    return f"EthicaBrowser — opening: {url}"


def browser_search(args: str = "") -> str:
    query = args.strip()
    if not query:
        return "Usage: browser search <query>"
    url = SEARCH_ENGINE + query.replace(" ", "+")
    return browser_open(url)


def browser_status(args: str = "") -> str:
    global _thread, _current_url
    if _thread and _thread.is_alive():
        return (
            f"EthicaBrowser — RUNNING\n"
            f"  URL : {_current_url or 'unknown'}"
        )
    return "EthicaBrowser — not running. Use: browser open <url>"


def browser_close(args: str = "") -> str:
    global _window, _thread
    if not _thread or not _thread.is_alive():
        return "EthicaBrowser — not running."
    if _window:
        try:
            _window.destroy()
            return "EthicaBrowser — closed."
        except Exception as e:
            return f"EthicaBrowser — close failed: {e}"
    return "EthicaBrowser — window not found."
