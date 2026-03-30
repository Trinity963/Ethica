# ============================================================
# Ethica v0.1 — notes.py
# Notes Module — sovereign note taking
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
import sys
import os
from datetime import datetime

MODULE_DIR  = Path(__file__).parent
ETHICA_ROOT = MODULE_DIR.parent.parent
NOTES_DIR   = ETHICA_ROOT / "memory" / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

def _get_notes():
    """Return sorted list of note files."""
    return sorted(NOTES_DIR.glob("note_*.txt"))

# ── Tool: note_save ───────────────────────────────────────────
def note_save(input_str):
    text = input_str.strip()
    if not text:
        return "Notes — nothing to save."
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = NOTES_DIR / f"note_{ts}.txt"
    filepath.write_text(text, encoding="utf-8")
    notes = _get_notes()
    return f"Notes — saved #{len(notes)}\n[{ts}] {text[:80]}"

# ── Tool: note_list ───────────────────────────────────────────
def note_list(input_str=""):
    notes = _get_notes()
    if not notes:
        return "Notes — no notes saved yet."
    lines = [f"Notes — {len(notes)} note(s)\n{'─'*40}"]
    for i, f in enumerate(notes, 1):
        ts = f.stem.replace("note_", "").replace("_", " ")
        preview = f.read_text(encoding="utf-8").strip()[:60]
        lines.append(f"#{i} [{ts}] {preview}...")
    return "\n".join(lines)

# ── Tool: note_read ───────────────────────────────────────────
def note_read(input_str):
    query = input_str.strip()
    notes = _get_notes()
    if not notes:
        return "Notes — no notes saved yet."
    # By number
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(notes):
            f = notes[idx]
            ts = f.stem.replace("note_", "").replace("_", " ")
            return f"Note #{idx+1} [{ts}]\n{'─'*40}\n{f.read_text(encoding='utf-8')}"
        return f"Notes — no note #{query}"
    # By keyword
    matches = [f for f in notes if query.lower() in f.read_text(encoding="utf-8").lower()]
    if not matches:
        return f"Notes — no notes matching: {query}"
    results = []
    for f in matches:
        ts = f.stem.replace("note_", "").replace("_", " ")
        results.append(f"[{ts}]\n{f.read_text(encoding='utf-8')}")
    return "\n\n".join(results)

# ── Tool: note_delete ─────────────────────────────────────────
def note_delete(input_str):
    query = input_str.strip()
    notes = _get_notes()
    if not notes:
        return "Notes — no notes to delete."
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(notes):
            f = notes[idx]
            preview = f.read_text(encoding="utf-8").strip()[:60]
            f.unlink()
            return f"Notes — deleted #{idx+1}: {preview}..."
        return f"Notes — no note #{query}"
    return "Notes — provide note number to delete."

# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "note_save":   note_save,
    "note_list":   note_list,
    "note_read":   note_read,
    "note_delete": note_delete,
}
def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[Notes] Unknown tool: {tool_name}"
