# ============================================================
# Ethica Module — trinity_scanner.py
# Trinity Folder Scanner
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Recursive directory scanner — produces timestamped JSON reports
# scanner_scan       — scan a directory (default depth 10)
# scanner_scan_depth — scan with custom depth (input: path|depth)
# scanner_last       — show summary of most recent scan
# ============================================================

import os
import json
from datetime import datetime
from pathlib import Path

# Output dir — relative to Ethica root
SCANS_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "scans"


def _do_scan(base_path, max_depth=10):
    """Core scan logic — returns (file_data, output_path) or raises."""
    base_path = os.path.expanduser(base_path.strip())
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Path not found: {base_path}")
    if not os.path.isdir(base_path):
        raise NotADirectoryError(f"Not a directory: {base_path}")

    file_data = []
    for root, dirs, files in os.walk(base_path):
        depth = root[len(base_path):].count(os.sep)
        if depth > max_depth:
            dirs.clear()
            continue
        for file in sorted(files):
            full_path = os.path.join(root, file)
            try:
                stat = os.stat(full_path)
                file_data.append({
                    "path": os.path.relpath(full_path, base_path),
                    "size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                file_data.append({
                    "path": os.path.relpath(full_path, base_path),
                    "error": str(e)
                })

    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = SCANS_DIR / f"scan_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scanned_path": base_path,
            "max_depth": max_depth,
            "timestamp": timestamp,
            "total_files": len(file_data),
            "files": file_data
        }, f, indent=2)

    return file_data, str(output_path)


def scanner_scan(input_str):
    """
    Tool: scanner_scan
    Input: /path/to/directory
    Scans recursively (depth 10) and saves JSON report.
    """
    path = input_str.strip()
    if not path:
        return "TrinityScanner — no path provided. Usage: scanner_scan /path/to/folder"
    try:
        file_data, output_path = _do_scan(path, max_depth=10)
        total = len(file_data)
        errors = sum(1 for f in file_data if "error" in f)
        return (
            "TrinityScanner ✓\n"
            f"Scanned: {path}\n"
            f"Files found: {total}\n"
            f"Errors: {errors}\n"
            f"Report saved: {output_path}"
        )
    except Exception as e:
        return f"TrinityScanner — scan error: {e}"


def scanner_scan_depth(input_str):
    """
    Tool: scanner_scan_depth
    Input: /path/to/directory|depth
    Scans with custom max depth.
    """
    parts = input_str.strip().split("|")
    if len(parts) != 2:
        return "TrinityScanner — usage: scanner_scan_depth /path/to/folder|4"
    path = parts[0].strip()
    try:
        depth = int(parts[1].strip())
    except ValueError:
        return f"TrinityScanner — invalid depth: {parts[1].strip()}"
    try:
        file_data, output_path = _do_scan(path, max_depth=depth)
        total = len(file_data)
        errors = sum(1 for f in file_data if "error" in f)
        return (
            f"TrinityScanner ✓\n"
            f"Scanned: {path} (depth {depth})\n"
            f"Files found: {total}\n"
            f"Errors: {errors}\n"
            f"Report saved: {output_path}"
        )
    except Exception as e:
        return f"TrinityScanner — scan error: {e}"


def scanner_last(input_str):
    """
    Tool: scanner_last
    Shows summary of the most recent scan report.
    """
    try:
        if not SCANS_DIR.exists():
            return "TrinityScanner — no scans yet. Run scanner_scan first."
        reports = sorted(SCANS_DIR.glob("scan_*.json"), reverse=True)
        if not reports:
            return "TrinityScanner — no scan reports found."
        latest = reports[0]
        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)
        total = data.get("total_files", 0)
        path  = data.get("scanned_path", "unknown")
        ts    = data.get("timestamp", "unknown")
        files = data.get("files", [])
        # Top 10 largest files
        sized = [f for f in files if "size_bytes" in f]
        sized.sort(key=lambda x: x["size_bytes"], reverse=True)
        top = sized[:10]
        lines = [
            "TrinityScanner — Last Report",
            f"Scanned: {path}",
            f"Timestamp: {ts}",
            f"Total files: {total}",
            "\nTop 10 largest files:"
        ]
        for f in top:
            kb = f["size_bytes"] / 1024
            lines.append(f"  {kb:.1f} KB — {f['path']}")
        lines.append(f"\nFull report: {latest}")
        return "\n".join(lines)
    except Exception as e:
        return f"TrinityScanner — error reading report: {e}"


# ── Module registry interface ─────────────────────────────────

TOOLS = {
    "scanner_scan":       scanner_scan,
    "scanner_scan_depth": scanner_scan_depth,
    "scanner_last":       scanner_last,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[TrinityScanner] Unknown tool: {tool_name}"
