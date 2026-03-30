# ============================================================
# Ethica v0.1 — config_manager.py
# User Configuration — portable, self-contained
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import json
import os

# ── Config lives inside the app directory — fully portable ────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.json")

# ── Defaults ──────────────────────────────────────────────────
DEFAULTS = {
    "theme":            "purple",
    "model":            "mistral",
    "ollama_host":      "http://localhost:11434",
    "font_size":        11,
    "user_name":        "Friend",
    "ethica_name":      "Ethica",
    "stream_responses": True,
    "show_timestamps":  True,
    "window_width":     900,
    "window_height":    680,
}


class ConfigManager:
    """
    Ethica Configuration Manager.
    Loads user settings from config/settings.json.
    Creates default config if none exists.
    All paths relative to app root — fully portable.
    """

    def __init__(self):
        self._config = {}
        self._path = CONFIG_PATH
        self._load()

    def _load(self):
        """Load config from disk. Creates defaults if missing."""
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge saved over defaults — new defaults fill in gaps
                self._config = {**DEFAULTS, **saved}
            except (json.JSONDecodeError, IOError):
                # Corrupted or unreadable — fall back to defaults
                self._config = dict(DEFAULTS)
        else:
            # First run — write defaults to disk
            self._config = dict(DEFAULTS)
            self.save()

    def get(self, key, fallback=None):
        """Get a config value by key."""
        return self._config.get(key, fallback)

    def set(self, key, value):
        """Set a config value. Call save() to persist."""
        self._config[key] = value

    def save(self):
        """Write current config to disk."""
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"[Ethica] Config save failed: {e}")

    def all(self):
        """Return full config dict."""
        return dict(self._config)

    def reset(self):
        """Reset to defaults and save."""
        self._config = dict(DEFAULTS)
        self.save()
