# ============================================================
# Ethica Module — dep_checker.py
# DepChecker Bridge — wraps Trinity's checker.py + auto_fixer.py
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Trinity's signature blocks are preserved intact.
# We wrap — never rewrite.
#
# Tools:
#   depchecker_scan   — full APT + PIP vulnerability scan
#   depchecker_fix    — auto-fix detected issues (V approves)
#   depchecker_report — show last scan report
# ============================================================

import os
import sys
import json

# ── Path setup — point to Trinity's modules ──────────────────
MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))

for p in [MODULE_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Import Trinity's tools ───────────────────────────────────
try:
    from checker    import DependencyChecker
    from auto_fixer import DependencyAutoFixer
    _LOADED = True
    _LOAD_ERROR = None
except Exception as e:
    _LOADED = False
    _LOAD_ERROR = str(e)

# ── Last report store ────────────────────────────────────────
_last_report = None


# ── Tool: depchecker_scan ────────────────────────────────────

def depchecker_scan(input_str):
    """
    Full APT + PIP dependency scan.
    Returns vulnerability report.
    """
    global _last_report

    if not _LOADED:
        return f"[DepChecker] Load error: {_LOAD_ERROR}"

    try:
        scanner = DependencyChecker()
        report  = scanner.run_scan()
        _last_report = report

        # Format for Ethica
        status = report.get("status", "Unknown")
        issues = report.get("issues", [])

        lines = [f"DepChecker Scan — {status}"]

        if issues:
            lines.append(f"\nIssues found ({len(issues)}):")
            for issue in issues:
                lines.append(f"  • {issue}")
            lines.append("\nRun depchecker_fix to resolve.")
        else:
            lines.append("\nAll packages clean.")

        # Save report to file for auto_fixer
        report_path = os.path.join(MODULE_DIR, "dependency_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)

        return "\n".join(lines)

    except Exception as e:
        return f"[DepChecker] Scan error: {e}"


# ── Tool: depchecker_fix ─────────────────────────────────────

def depchecker_fix(input_str):
    """
    Auto-fix detected dependency issues.
    V approves before this runs — manual tool only.
    """
    global _last_report

    if not _LOADED:
        return f"[DepChecker] Load error: {_LOAD_ERROR}"

    if not _last_report:
        # Try loading from file
        report_path = os.path.join(MODULE_DIR, "dependency_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                _last_report = json.load(f)
        else:
            return "[DepChecker] No scan report found. Run depchecker_scan first."

    issues = _last_report.get("issues", [])
    if not issues:
        return "[DepChecker] No issues to fix."

    try:
        fixer = DependencyAutoFixer(issues)
        fixer.execute_fixes()
        return f"[DepChecker] Fixed {len(issues)} issue(s). Re-run depchecker_scan to verify."
    except Exception as e:
        return f"[DepChecker] Fix error: {e}"


# ── Tool: depchecker_report ──────────────────────────────────

def depchecker_report(input_str):
    """Show last scan report."""
    global _last_report

    if not _last_report:
        report_path = os.path.join(MODULE_DIR, "dependency_report.json")
        if os.path.exists(report_path):
            with open(report_path) as f:
                _last_report = json.load(f)
        else:
            return "[DepChecker] No report yet. Run depchecker_scan first."

    status = _last_report.get("status", "Unknown")
    issues = _last_report.get("issues", [])

    lines = [f"DepChecker Last Report — {status}"]
    if issues:
        for issue in issues:
            lines.append(f"  • {issue}")
    else:
        lines.append("  All packages clean.")

    return "\n".join(lines)


# ── Module registry interface ────────────────────────────────

TOOLS = {
    "depchecker_scan":   depchecker_scan,
    "depchecker_fix":    depchecker_fix,
    "depchecker_report": depchecker_report,
}

def get_tools():
    return TOOLS

def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    if fn:
        return fn(input_str)
    return f"[DepChecker] Unknown tool: {tool_name}"
