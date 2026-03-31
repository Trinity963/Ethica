# ============================================================
# Ethica v0.1 — diff_tool.py
# Diff Tool Module — compare files and directories
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
import difflib
MODULE_DIR  = Path(__file__).parent

def _expand(path_str):
    return Path(path_str.strip()).expanduser()

def _parse_two_paths(input_str):
    """Parse 'path1 | path2' or 'path1 > path2' input."""
    sep = "|" if "|" in input_str else ">"
    if sep not in input_str:
        return None, None, "Usage: diff_files: ~/file1 | ~/file2"
    parts = input_str.split(sep, 1)
    return _expand(parts[0].strip()), _expand(parts[1].strip()), None

# ── Tool: diff_files ──────────────────────────────────────────
def diff_files(input_str):
    src, dst, err = _parse_two_paths(input_str)
    if err:
        return f"DiffTool — {err}"
    if not src.exists():
        return f"DiffTool — file not found: {src}"
    if not dst.exists():
        return f"DiffTool — file not found: {dst}"

    try:
        a = src.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        b = dst.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    except Exception as e:
        return f"DiffTool — read error: {e}"

    diff = list(difflib.unified_diff(
        a, b,
        fromfile=str(src),
        tofile=str(dst),
        lineterm=""
    ))

    if not diff:
        return f"DiffTool — files are identical:\n{src}\n{dst}"

    added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

    diff_text = "\n".join(diff)
    if len(diff_text) > 3000:
        diff_text = "\n".join(diff[:80]) + "\n... truncated ..."

    summary = f"DiffTool — {src.name} vs {dst.name}\n+{added} added  -{removed} removed\n{'─'*40}\n"

    # Push to canvas debug tab via marker
    return summary + f"[DEBUG:Diff:diff:\n{diff_text}\n]"

# ── Tool: diff_dirs ───────────────────────────────────────────
def diff_dirs(input_str):
    src, dst, err = _parse_two_paths(input_str)
    if err:
        return f"DiffTool — {err}"
    if not src.exists() or not src.is_dir():
        return f"DiffTool — directory not found: {src}"
    if not dst.exists() or not dst.is_dir():
        return f"DiffTool — directory not found: {dst}"

    src_files = {f.relative_to(src) for f in src.rglob("*") if f.is_file()}
    dst_files = {f.relative_to(dst) for f in dst.rglob("*") if f.is_file()}

    added   = dst_files - src_files
    removed = src_files - dst_files
    common  = src_files & dst_files

    modified = []
    for f in common:
        try:
            a = (src / f).read_bytes()
            b = (dst / f).read_bytes()
            if a != b:
                modified.append(f)
        except Exception:
            pass

    lines = [
        f"DiffTool — {src.name} vs {dst.name}\n{'─'*40}",
        f"✓ Identical: {len(common) - len(modified)}",
        f"~ Modified:  {len(modified)}",
        f"+ Added:     {len(added)}",
        f"- Removed:   {len(removed)}",
        ""
    ]
    if modified:
        lines.append("~ Modified:")
        lines += [f"  ~ {f}" for f in sorted(modified)[:20]]
    if added:
        lines.append("+ Added:")
        lines += [f"  + {f}" for f in sorted(added)[:20]]
    if removed:
        lines.append("- Removed:")
        lines += [f"  - {f}" for f in sorted(removed)[:20]]

    return "\n".join(lines)

# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "diff_files": diff_files,
    "diff_dirs":  diff_dirs,
}
def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[DiffTool] Unknown tool: {tool_name}"
