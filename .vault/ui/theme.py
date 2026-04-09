# ============================================================
# Ethica v0.1 — theme.py
# UI Theme Engine — Purple default, user selectable
# Live refresh via observer pattern
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import logging

THEMES = {

    "purple": {
        "name": "Purple",
        "description": "Victory's palette — default",
        "bg_primary":       "#1a0a2e",
        "bg_secondary":     "#2d1b4e",
        "bg_tertiary":      "#3d2660",
        "bg_input":         "#241340",
        "bg_chat":          "#150820",
        "text_primary":     "#e8d5ff",
        "text_secondary":   "#b39ddb",
        "text_muted":       "#7e6b9e",
        "text_user":        "#f3e5ff",
        "text_ethica":      "#d4b8ff",
        "accent_primary":   "#9b59b6",
        "accent_bright":    "#c39bd3",
        "accent_glow":      "#7d3c98",
        "accent_soft":      "#6c3483",
        "bubble_user":      "#4a235a",
        "bubble_ethica":    "#2d1b4e",
        "bubble_border":    "#6c3483",
        "button_bg":        "#7d3c98",
        "button_hover":     "#9b59b6",
        "button_active":    "#5b2c6f",
        "button_text":      "#f3e5ff",
        "scrollbar_bg":     "#2d1b4e",
        "scrollbar_thumb":  "#7d3c98",
        "status_online":    "#82e0aa",
        "status_offline":   "#e74c3c",
        "status_thinking":  "#f39c12",
        "border":           "#4a235a",
        "separator":        "#3d2660",
        "highlight":        "#c39bd3",
    },

    "midnight": {
        "name": "Midnight",
        "description": "Deep dark — easy on the eyes",
        "bg_primary":       "#0d0d0d",
        "bg_secondary":     "#1a1a1a",
        "bg_tertiary":      "#252525",
        "bg_input":         "#111111",
        "bg_chat":          "#080808",
        "text_primary":     "#e0e0e0",
        "text_secondary":   "#a0a0a0",
        "text_muted":       "#606060",
        "text_user":        "#ffffff",
        "text_ethica":      "#c8c8c8",
        "accent_primary":   "#3d8bcd",
        "accent_bright":    "#5dade2",
        "accent_glow":      "#2e86c1",
        "accent_soft":      "#1a5276",
        "bubble_user":      "#1a2a3a",
        "bubble_ethica":    "#1a1a1a",
        "bubble_border":    "#2e4057",
        "button_bg":        "#2e86c1",
        "button_hover":     "#3498db",
        "button_active":    "#1a5276",
        "button_text":      "#ffffff",
        "scrollbar_bg":     "#1a1a1a",
        "scrollbar_thumb":  "#2e86c1",
        "status_online":    "#82e0aa",
        "status_offline":   "#e74c3c",
        "status_thinking":  "#f39c12",
        "border":           "#2a2a2a",
        "separator":        "#222222",
        "highlight":        "#5dade2",
    },

    "forest": {
        "name": "Forest",
        "description": "Grounded — deep greens",
        "bg_primary":       "#0a1a0f",
        "bg_secondary":     "#122a18",
        "bg_tertiary":      "#1a3d22",
        "bg_input":         "#0d2013",
        "bg_chat":          "#070f09",
        "text_primary":     "#d5f0dc",
        "text_secondary":   "#96c9a0",
        "text_muted":       "#5a8a63",
        "text_user":        "#eaf7ec",
        "text_ethica":      "#c2e8c9",
        "accent_primary":   "#27ae60",
        "accent_bright":    "#2ecc71",
        "accent_glow":      "#1e8449",
        "accent_soft":      "#145a32",
        "bubble_user":      "#1a3d22",
        "bubble_ethica":    "#122a18",
        "bubble_border":    "#27ae60",
        "button_bg":        "#1e8449",
        "button_hover":     "#27ae60",
        "button_active":    "#145a32",
        "button_text":      "#eaf7ec",
        "scrollbar_bg":     "#122a18",
        "scrollbar_thumb":  "#27ae60",
        "status_online":    "#2ecc71",
        "status_offline":   "#e74c3c",
        "status_thinking":  "#f39c12",
        "border":           "#1a3d22",
        "separator":        "#122a18",
        "highlight":        "#2ecc71",
    },

    "ember": {
        "name": "Ember",
        "description": "Warm — amber and deep red",
        "bg_primary":       "#1a0a00",
        "bg_secondary":     "#2d1500",
        "bg_tertiary":      "#3d1f00",
        "bg_input":         "#200e00",
        "bg_chat":          "#100600",
        "text_primary":     "#fde8c8",
        "text_secondary":   "#d4956a",
        "text_muted":       "#8a5a35",
        "text_user":        "#fff3e0",
        "text_ethica":      "#f0d0a0",
        "accent_primary":   "#e67e22",
        "accent_bright":    "#f39c12",
        "accent_glow":      "#ca6f1e",
        "accent_soft":      "#784212",
        "bubble_user":      "#4a1f00",
        "bubble_ethica":    "#2d1500",
        "bubble_border":    "#e67e22",
        "button_bg":        "#ca6f1e",
        "button_hover":     "#e67e22",
        "button_active":    "#784212",
        "button_text":      "#fff3e0",
        "scrollbar_bg":     "#2d1500",
        "scrollbar_thumb":  "#e67e22",
        "status_online":    "#82e0aa",
        "status_offline":   "#e74c3c",
        "status_thinking":  "#f39c12",
        "border":           "#4a1f00",
        "separator":        "#3d1f00",
        "highlight":        "#f39c12",
    },

    "arctic": {
        "name": "Arctic",
        "description": "Clean — cool whites and steel",
        "bg_primary":       "#f0f4f8",
        "bg_secondary":     "#e2e8f0",
        "bg_tertiary":      "#cbd5e0",
        "bg_input":         "#ffffff",
        "bg_chat":          "#f8fafc",
        "text_primary":     "#1a202c",
        "text_secondary":   "#4a5568",
        "text_muted":       "#a0aec0",
        "text_user":        "#1a202c",
        "text_ethica":      "#2d3748",
        "accent_primary":   "#4299e1",
        "accent_bright":    "#63b3ed",
        "accent_glow":      "#3182ce",
        "accent_soft":      "#bee3f8",
        "bubble_user":      "#ebf8ff",
        "bubble_ethica":    "#ffffff",
        "bubble_border":    "#bee3f8",
        "button_bg":        "#3182ce",
        "button_hover":     "#4299e1",
        "button_active":    "#2b6cb0",
        "button_text":      "#ffffff",
        "scrollbar_bg":     "#e2e8f0",
        "scrollbar_thumb":  "#4299e1",
        "status_online":    "#38a169",
        "status_offline":   "#e53e3e",
        "status_thinking":  "#d69e2e",
        "border":           "#e2e8f0",
        "separator":        "#cbd5e0",
        "highlight":        "#63b3ed",
    },
}

# ── Font Definitions ──────────────────────────────────────────

FONTS = {
    "title":        ("Georgia", 16, "bold"),
    "heading":      ("Georgia", 13, "bold"),
    "body":         ("Helvetica", 11),
    "body_bold":    ("Helvetica", 11, "bold"),
    "small":        ("Helvetica", 9),
    "mono":         ("Courier", 10),
    "input":        ("Helvetica", 12),
    "button":       ("Helvetica", 10, "bold"),
    "status":       ("Helvetica", 9),
    "timestamp":    ("Helvetica", 8),
}

DEFAULT_THEME = "purple"

# ── Theme Engine ──────────────────────────────────────────────

class ThemeEngine:
    """
    Ethica Theme Engine.
    Observer pattern — components register their apply_theme()
    method. On switch(), all listeners are notified and repaint
    themselves. No restart needed.
    """

    def __init__(self, theme_name=None):
        self._active = theme_name or DEFAULT_THEME
        if self._active not in THEMES:
            self._active = DEFAULT_THEME
        self._listeners = []

    @property
    def active(self):
        return self._active

    @property
    def colors(self):
        return THEMES[self._active]

    def get(self, key, fallback="#ffffff"):
        return THEMES[self._active].get(key, fallback)

    def font(self, key):
        return FONTS.get(key, FONTS["body"])

    def register(self, callback):
        """Register a component's apply_theme() for live refresh."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def switch(self, theme_name):
        """
        Switch theme and notify all registered components to repaint.
        Returns True if successful.
        """
        if theme_name in THEMES:
            self._active = theme_name
            self._notify()
            return True
        return False

    def _notify(self):
        """Fire all registered apply_theme() callbacks."""
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                logging.warning("[Ethica] Theme refresh error in %s: %s", callback, e)

    def available_themes(self):
        return [(k, v["name"], v["description"]) for k, v in THEMES.items()]

    def theme_names(self):
        return list(THEMES.keys())


# ── Module-level instance ─────────────────────────────────────

theme = ThemeEngine()
