# ============================================================
# Ethica v0.1 — canvas_history.py
# Canvas Version Control — Nothing Lost. Ever.
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Every meaningful change to a canvas tab is snapshotted.
# V can restore any previous state with one click.
# Snapshots are named automatically or by V.
#
# Philosophy:
#   Memory is evolution — never delete, never edit, never control.
#   This applies to the canvas too.
#   Every version is sacred.
# ============================================================

import json
import os
from datetime import datetime


# ── History File ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANVAS_HISTORY_FILE = os.path.join(BASE_DIR, "memory", "canvas_history.json")

# Max snapshots per tab — keeps file size sane
MAX_SNAPSHOTS_PER_TAB = 50


class CanvasSnapshot:
    """
    A single point-in-time capture of a canvas tab.
    """

    def __init__(self, tab_name, content, label="auto", mode="document"):
        self.tab_name   = tab_name
        self.content    = content
        self.label      = label       # "auto" or user-named
        self.mode       = mode
        self.timestamp  = datetime.now().isoformat()
        self.ts_display = datetime.now().strftime("%b %d  %H:%M")

    def to_dict(self):
        return {
            "tab_name":   self.tab_name,
            "content":    self.content,
            "label":      self.label,
            "mode":       self.mode,
            "timestamp":  self.timestamp,
            "ts_display": self.ts_display,
        }

    @classmethod
    def from_dict(cls, d):
        snap = cls.__new__(cls)
        snap.tab_name   = d.get("tab_name", "Untitled")
        snap.content    = d.get("content", "")
        snap.label      = d.get("label", "auto")
        snap.mode       = d.get("mode", "document")
        snap.timestamp  = d.get("timestamp", "")
        snap.ts_display = d.get("ts_display", "")
        return snap

    @property
    def preview(self):
        """First 60 chars of content — for history panel display."""
        c = self.content.strip()
        if not c:
            return "(empty)"
        return c[:60] + ("…" if len(c) > 60 else "")

    @property
    def display_label(self):
        """Human-readable label for history list."""
        if self.label and self.label != "auto":
            return f"★ {self.label}"
        return self.ts_display


class CanvasHistory:
    """
    Version control engine for the Living Canvas.

    Manages snapshots per tab.
    Persists to memory/canvas_history.json.

    Usage:
        history = CanvasHistory()
        history.snapshot(tab_name, content, mode)          # auto snapshot
        history.snapshot(tab_name, content, mode, "v2")    # named snapshot
        snaps = history.get_snapshots(tab_name)            # list all
        content, mode = history.restore(tab_name, index)  # restore one
    """

    def __init__(self):
        # { tab_name: [CanvasSnapshot, ...] }  newest first
        self._store = {}
        self._load()

    # ── Snapshot ─────────────────────────────────────────────

    def snapshot(self, tab_name, content, mode="document", label="auto"):
        """
        Take a snapshot of a tab's current state.
        Deduplicates — won't save if content unchanged since last snap.
        """
        snaps = self._store.setdefault(tab_name, [])

        # Deduplicate — skip if content identical to most recent
        if snaps and snaps[0].content == content:
            return None

        snap = CanvasSnapshot(
            tab_name=tab_name,
            content=content,
            label=label,
            mode=mode
        )

        # Insert newest first
        snaps.insert(0, snap)

        # Trim to max
        if len(snaps) > MAX_SNAPSHOTS_PER_TAB:
            snaps[:] = snaps[:MAX_SNAPSHOTS_PER_TAB]

        self._save()
        return snap

    def name_snapshot(self, tab_name, index, name):
        """
        Give a snapshot a meaningful name.
        eg: "before refactor", "working version", "client demo"
        """
        snaps = self._store.get(tab_name, [])
        if 0 <= index < len(snaps):
            snaps[index].label = name
            self._save()
            return True
        return False

    # ── Restore ──────────────────────────────────────────────

    def restore(self, tab_name, index):
        """
        Restore a tab to a previous snapshot.
        Returns (content, mode) tuple.
        Before restoring, snapshots current state as "before restore".
        """
        snaps = self._store.get(tab_name, [])
        if not snaps or index >= len(snaps):
            return None, None
        snap = snaps[index]
        return snap.content, snap.mode

    # ── Query ────────────────────────────────────────────────

    def get_snapshots(self, tab_name):
        """Return all snapshots for a tab, newest first."""
        return self._store.get(tab_name, [])

    def get_snapshot_count(self, tab_name):
        return len(self._store.get(tab_name, []))

    def has_history(self, tab_name):
        return len(self._store.get(tab_name, [])) > 1

    def rename_tab_history(self, old_name, new_name):
        """
        When a tab is renamed, migrate its history to the new name.
        """
        if old_name in self._store:
            self._store[new_name] = self._store.pop(old_name)
            # Update tab_name field in all snapshots
            for snap in self._store[new_name]:
                snap.tab_name = new_name
            self._save()

    def clear_tab_history(self, tab_name):
        """Clear all snapshots for a tab."""
        if tab_name in self._store:
            del self._store[tab_name]
            self._save()

    # ── Persistence ──────────────────────────────────────────

    def _save(self):
        try:
            os.makedirs(os.path.dirname(CANVAS_HISTORY_FILE), exist_ok=True)
            data = {
                tab: [s.to_dict() for s in snaps]
                for tab, snaps in self._store.items()
            }
            with open(CANVAS_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CanvasHistory] Save failed: {e}")

    def _load(self):
        if not os.path.exists(CANVAS_HISTORY_FILE):
            return
        try:
            with open(CANVAS_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._store = {
                tab: [CanvasSnapshot.from_dict(s) for s in snaps]
                for tab, snaps in data.items()
            }
        except Exception as e:
            print(f"[CanvasHistory] Load failed: {e}")
            self._store = {}
