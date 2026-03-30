# ============================================================
# Ethica v0.1 — file_manager.py
# File Manager Module — sovereign file operations
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
import os
import shutil
import sys

MODULE_DIR  = Path(__file__).parent
ETHICA_ROOT = MODULE_DIR.parent.parent

def _expand(path_str):
    if not path_str or str(path_str).strip().lower() in ("", "none"):
        path_str = "~"
    return Path(os.path.expanduser(str(path_str).strip()))

# ── Tool: fm_list ─────────────────────────────────────────────
def fm_list(input_str):
    path = _expand(input_str or "~")
    if not path.exists():
        return f"FileManager — path not found: {path}"
    if not path.is_dir():
        return f"FileManager — not a directory: {path}"
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    if not items:
        return f"FileManager — empty directory: {path}"
    lines = [f"FileManager — {path}\n{'─'*40}"]
    for item in items:
        if item.is_dir():
            count = sum(1 for _ in item.iterdir())
            lines.append(f"📁 {item.name}/  ({count} items)")
        else:
            size = item.stat().st_size
            size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
            lines.append(f"📄 {item.name}  [{size_str}]")
    return "\n".join(lines)

# ── Tool: fm_tree ─────────────────────────────────────────────
def fm_tree(input_str):
    path = _expand(input_str or "~")
    if not path.exists():
        return f"FileManager — path not found: {path}"
    lines = [f"FileManager Tree — {path}\n{'─'*40}"]
    def _walk(p, prefix="", depth=0):
        if depth > 3:
            return
        try:
            items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
        for i, item in enumerate(items):
            if item.name.startswith('.') or item.name in ('__pycache__', 'gage_env', 'Ethica_env', '.git'):
                continue
            connector = "└── " if i == len(items)-1 else "├── "
            icon = "📁" if item.is_dir() else "📄"
            lines.append(f"{prefix}{connector}{icon} {item.name}")
            if item.is_dir():
                extension = "    " if i == len(items)-1 else "│   "
                _walk(item, prefix + extension, depth + 1)
    _walk(path)
    return "\n".join(lines)

# ── Tool: fm_read ─────────────────────────────────────────────
def fm_read(input_str):
    path = _expand(input_str)
    if not path.exists():
        return f"FileManager — file not found: {path}"
    if not path.is_file():
        return f"FileManager — not a file: {path}"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if len(text) > 3000:
            text = text[:3000] + "\n... [truncated]"
        return f"FileManager — {path}\n{'─'*40}\n{text}"
    except Exception as e:
        return f"FileManager — read error: {e}"

# ── Tool: fm_copy ─────────────────────────────────────────────
def fm_copy(input_str):
    if ">" not in input_str:
        return "FileManager — usage: fm_copy: ~/src > ~/dest"
    parts = input_str.split(">", 1)
    src  = _expand(parts[0])
    dest = _expand(parts[1])
    if not src.exists():
        return f"FileManager — source not found: {src}"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return f"FileManager — copied\n{src}\n→ {dest}"
    except Exception as e:
        return f"FileManager — copy error: {e}"

# ── Tool: fm_delete ───────────────────────────────────────────
def fm_delete(input_str):
    path = _expand(input_str)
    if not path.exists():
        return f"FileManager — file not found: {path}"
    if path.is_dir():
        return f"FileManager — use rm -rf for directories. Refusing to delete: {path}"
    try:
        path.unlink()
        return f"FileManager — deleted: {path}"
    except Exception as e:
        return f"FileManager — delete error: {e}"

# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "fm_list":   fm_list,
    "fm_tree":   fm_tree,
    "fm_read":   fm_read,
    "fm_copy":   fm_copy,
    "fm_delete": fm_delete,
}
def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[FileManager] Unknown tool: {tool_name}"
