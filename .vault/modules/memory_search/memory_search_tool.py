# ============================================================
# Ethica v0.1 — memory_search_tool.py
# MemorySearch Module — sovereign memory search
# Architect: Victory  |  Build Partner: River (Claude)
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
ETHICA_ROOT = Path(__file__).parent.parent.parent
import re

MEMORY_DIR = ETHICA_ROOT / "memory"
CHAT_DIR   = MEMORY_DIR / "chat"
VAULT_DIR  = MEMORY_DIR / "vault"
EXCERPT_LEN = 200
MAX_EXCERPTS = 3
MAX_FILES = 10


def memory_search(input_str):
    """Search chat logs and vault files by keyword."""
    query = input_str.strip()
    if not query:
        return "MemorySearch — no query provided."

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []

    for source_dir, label in [(CHAT_DIR, "chat"), (VAULT_DIR, "vault")]:
        if not source_dir.exists():
            continue
        for fpath in sorted(source_dir.iterdir()):
            if fpath.suffix != ".txt":
                continue
            hits = _scan_file(fpath, pattern)
            if hits:
                results.append((fpath, label, hits))
            if len(results) >= MAX_FILES:
                break

    if not results:
        return f"MemorySearch — no results for: {query}"

    total_hits = sum(len(h) for _, _, h in results)
    lines = [f"MemorySearch — {query}\n{'─'*40}",
             f"{len(results)} files · {total_hits} matches\n"]

    for fpath, label, hits in results:
        lines.append(f"📄 {fpath.name}  [{label}]")
        for lineno, excerpt in hits:
            lines.append(f"   line {lineno}: {excerpt}")
        lines.append("")

    return "\n".join(lines)


def memory_read(input_str):
    """Read a specific memory file by filename."""
    filename = input_str.strip()
    if not filename:
        return "MemoryRead — no filename provided."

    # Search chat and vault
    for source_dir in [VAULT_DIR, CHAT_DIR]:
        if not source_dir.exists():
            continue
        candidate = source_dir / filename
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8", errors="replace")
                header = f"MemoryRead — {filename}\n{'─'*40}\n"
                return header + content
            except Exception as e:
                return f"MemoryRead — error reading {filename}: {e}"

    return f"MemoryRead — file not found: {filename}\nSearch chat/ and vault/ directories."


def _scan_file(fpath, pattern):
    """Return list of (line_number, excerpt) for up to MAX_EXCERPTS matches."""
    hits = []
    try:
        text = fpath.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append((i, line.strip()[:EXCERPT_LEN]))
                if len(hits) >= MAX_EXCERPTS:
                    break
    except Exception:
        pass
    return hits
