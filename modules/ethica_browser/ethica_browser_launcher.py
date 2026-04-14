#!/usr/bin/env python3
# EthicaBrowser launcher — runs as subprocess, owns its own main thread.
import os
import sys

# Force software rendering — fixes black screen on systems without GPU acceleration
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"

import webview

def main():
    if len(sys.argv) < 2:
        print("Usage: ethica_browser_launcher.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    window = webview.create_window(
        "EthicaBrowser — Sovereign",
        url,
        width=1200,
        height=800,
        resizable=True,
    )
    webview.start()

if __name__ == "__main__":
    main()
