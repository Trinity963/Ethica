# ============================================================
# Ethica Module — wormbot.py
# WormBot Bridge — wraps ~/Ethica/modules/worm_bot
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Calls worm_bot's own modules directly.
# analyze_code() → find issues
# fix_code()     → apply fixes
# Routes fixed code to debug tab via [DEBUG:] push.
#
# Auto-fix policy:
#   Python JS CSS HTML — ON
#   Rust               — OFF (V reviews)
# ============================================================

import os
import sys
import difflib
from datetime import datetime

# ── Path setup — point to worm_bot's own modules ─────────────

MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
WORMBOT_DIR  = os.path.join(MODULE_DIR, "..", "worm_bot")
WORMBOT_MODS = os.path.join(WORMBOT_DIR, "modules")

# Insert worm_bot paths so its imports resolve correctly
for p in [WORMBOT_DIR, WORMBOT_MODS]:
    if p not in sys.path:
        sys.path.insert(0, os.path.abspath(p))


# ── Lazy module loader ────────────────────────────────────────

_loaded = {}

def _get_module(lang):
    """Load and cache a worm_bot language module."""
    if lang in _loaded:
        return _loaded[lang]

    try:
        if lang == "python":
            from python_module import PythonModule
            _loaded[lang] = PythonModule()
        elif lang in ("javascript", "js"):
            from js_module import JSModule
            _loaded["javascript"] = JSModule()
            _loaded["js"]         = _loaded["javascript"]
        elif lang == "css":
            from css_module import CSSModule
            _loaded[lang] = CSSModule()
        elif lang == "html":
            from html_module import HTMLModule
            _loaded[lang] = HTMLModule()
        elif lang in ("rust", "rs"):
            from rust_module import RustModule
            _loaded["rust"] = RustModule()
            _loaded["rs"]   = _loaded["rust"]
        elif lang == "json":
            from json_module import JSONModule
            _loaded[lang] = JSONModule()
        elif lang in ("markdown", "md"):
            from markdown_module import MarkdownModule
            _loaded["markdown"] = MarkdownModule()
            _loaded["md"]       = _loaded["markdown"]
        elif lang in ("bash", "sh"):
            from bash_module import BashModule
            _loaded["bash"] = BashModule()
            _loaded["sh"]   = _loaded["bash"]
        else:
            return None
    except ImportError as e:
        return f"ImportError loading {lang} module: {e}"

    return _loaded.get(lang)


# ── State ─────────────────────────────────────────────────────

_last_result = None
_report_log  = []

AUTO_FIX = {
    "python":     False,
    "javascript": False,
    "js":         False,
    "css":        False,
    "html":       False,
    "rust":       False,
    "rs":         False,
    "json":       False,
    "markdown":   False,
    "md":         False,
}

EXT_MAP = {
    ".py":   "python",
    ".js":   "javascript",
    ".css":  "css",
    ".html": "html",
    ".htm":  "html",
    ".rs":   "rust",
    ".json": "json",
    ".md":   "markdown",
    ".sh":   "bash",
}

SUPPORTED = "python, javascript, css, html, rust, json, markdown"


# ── Tool: wormbot_fix ─────────────────────────────────────────

def wormbot_fix(input_str):
    """
    Analyze and fix code inline.
    Input: "language|code"
    """
    global _last_result

    if '|' in input_str:
        lang, _, code = input_str.partition('|')
        lang = lang.strip().lower()
        code = code.strip()
    else:
        code = input_str.strip()
        lang = _detect_language(code)

    if not code:
        return "No code provided. Usage: [TOOL:wormbot_fix: python|your code here]"

    mod = _get_module(lang)
    if mod is None:
        return f"Unsupported language: '{lang}'. Supported: {SUPPORTED}"
    if isinstance(mod, str):
        return mod  # error string

    result = _run_analysis(lang, code, mod)
    _last_result = result
    _log_activity("fix", lang, result)

    return _format_result(result)


# ── Tool: wormbot_scan ────────────────────────────────────────

def wormbot_scan(input_str):
    """
    Scan a file on disk — analyze and fix in place.
    Input: file path
    """
    global _last_result

    filepath = input_str.strip()
    if not filepath:
        return "No file path provided."

    # Resolve ~, missing /home/trinity prefix, and bare filenames
    from pathlib import Path
    import glob as _glob
    p = Path(filepath).expanduser()
    if not p.is_absolute():
        p = Path(os.path.expanduser("~") + "/Ethica") / p
    # Bare filename fallback — search ~/Ethica recursively
    if not p.exists():
        name = Path(filepath).name
        if name and "." in name:
            ethica_root = Path(os.path.expanduser("~/Ethica"))
            matches = [m for m in ethica_root.rglob(name)
                       if ".git" not in m.parts and "Ethica_env" not in m.parts
                       and "__pycache__" not in m.parts]
            if matches:
                p = matches[0]
    filepath = str(p)

    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    if os.path.isdir(filepath):
        return f"WormBot scans files, not directories: {filepath}"

    ext  = os.path.splitext(filepath)[1].lower()
    lang = EXT_MAP.get(ext)
    if not lang:
        return f"Unsupported file type: {ext}. Supported: .py .js .css .html .rs .json .md"

    mod = _get_module(lang)
    if mod is None:
        return f"No module for {lang}"
    if isinstance(mod, str):
        return mod

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return f"Could not read file: {e}"

    result              = _run_analysis(lang, code, mod)
    result["filepath"]  = filepath
    _last_result        = result
    _log_activity("scan", lang, result)

    # Write fix in place if auto-fix on
    if result["auto_fixed"] and AUTO_FIX.get(lang, False):
        fixed_code = result["fixed_code"]

        # Surgical gate — verify fixed code is syntactically clean before writing
        if lang == "python":
            import ast as _ast
            try:
                _ast.parse(fixed_code)
            except SyntaxError as e:
                return (
                    _format_result(result) +
                    f"\n\n⚠ Auto-fix aborted — fixed code has syntax error at line {e.lineno}: {e.msg}\n"
                    f"Original file unchanged."
                )

        # Verify fix actually differs from original
        if fixed_code.strip() == code.strip():
            result["_status_note"] = "No changes needed — file unchanged."
            return _format_result(result)

        backup = filepath + ".worm_backup"
        try:
            with open(backup, "w", encoding="utf-8") as f:
                f.write(code)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            result["_status_note"] = f"✓ File updated: {filepath}\nBackup: {backup}"
            return _format_result(result)
        except Exception as e:
            result["_status_note"] = f"Could not write fix: {e}"
            return _format_result(result)

    return _format_result(result)


# ── Tool: wormbot_diff ────────────────────────────────────────

def wormbot_diff(input_str):
    """Show diff between original and fixed code from last run."""
    if not _last_result:
        return "No previous WormBot run. Run wormbot_fix or wormbot_scan first."

    original = _last_result.get("original_code", "")
    fixed    = _last_result.get("fixed_code", "")

    if not fixed:
        return "Last run produced no fixes."

    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile="original",
        tofile="fixed",
        lineterm=""
    ))
    return "Diff:\n" + "".join(diff) if diff else "No differences."


# ── Tool: wormbot_report ──────────────────────────────────────

def wormbot_report(input_str):
    """Activity report for this session."""
    if not _report_log:
        return "No WormBot activity this session."

    total  = len(_report_log)
    fixed  = sum(1 for r in _report_log if r["auto_fixed"])
    broken = sum(1 for r in _report_log if r["status"] == "broken")
    clean  = sum(1 for r in _report_log if r["status"] == "clean")
    langs  = {}
    for r in _report_log:
        langs[r["lang"]] = langs.get(r["lang"], 0) + 1

    lines = [
        f"WormBot — {total} operation(s) this session",
        f"  {broken} broken  |  {clean} clean  |  {fixed} auto-fixed",
        f"  Languages: " + ", ".join(f"{l}×{n}" for l, n in langs.items()),
        "",
        "Recent:"
    ]
    for r in _report_log[-5:]:
        s = "✓" if r["status"] == "clean" else "✗"
        f = " → fixed" if r["auto_fixed"] else ""
        lines.append(f"  {s} {r['lang']:12} {r['issues']} issue(s){f}  {r['time']}")

    return "\n".join(lines)


# ── Tool: wormbot_apply ───────────────────────────────────────

def wormbot_apply(input_str):
    """Apply last Rust suggestion after V review."""
    if not _last_result:
        return "No previous result."

    lang = _last_result.get("lang", "")
    if lang not in ("rust", "rs"):
        return "wormbot_apply is only for Rust — other languages auto-fix."

    fixed = _last_result.get("fixed_code")
    if not fixed:
        return "No fix was generated."

    filepath = input_str.strip() or _last_result.get("filepath", "")
    if not filepath:
        return "No file path provided."

    try:
        backup = filepath + ".worm_backup"
        with open(filepath, "r") as f:
            orig = f.read()
        with open(backup, "w") as f:
            f.write(orig)
        with open(filepath, "w") as f:
            f.write(fixed)
        return f"Applied to: {filepath}\nBackup: {backup}"
    except Exception as e:
        return f"Could not apply: {e}"


# ── Core analysis runner ──────────────────────────────────────

def _run_analysis(lang, code, mod):
    """Call worm_bot module's analyze_code and fix_code."""
    issues     = []
    fixed_code = None
    auto_fixed = False

    try:
        analysis = mod.analyze_code(code)
        issues   = analysis.get("issues", [])
    except Exception as e:
        issues = [f"Analysis error: {e}"]

    can_fix = AUTO_FIX.get(lang, False) and bool(issues)

    if can_fix:
        try:
            fixed = mod.fix_code(code)
            if fixed and fixed != code:
                fixed_code = fixed
                auto_fixed = True
        except Exception as e:
            issues.append(f"Fix error: {e}")

    return {
        "lang":          lang,
        "status":        "clean" if not issues else "broken",
        "issues":        issues,
        "original_code": code,
        "fixed_code":    fixed_code,
        "auto_fixed":    auto_fixed,
        "timestamp":     datetime.now().isoformat(),
    }


# ── Formatter ─────────────────────────────────────────────────

def _format_result(result):
    lang      = result.get("lang", "unknown")
    status    = result.get("status", "unknown")
    issues    = result.get("issues", [])
    auto      = result.get("auto_fixed", False)
    fixed     = result.get("fixed_code", "")
    original  = result.get("original_code", "")

    lines = [f"WormBot — {lang}  {'✓ clean' if status == 'clean' else '✗ broken'}"]

    if issues:
        lines.append(f"\nIssues ({len(issues)}):")
        for i in issues:
            lines.append(f"  • {i}")
    else:
        lines.append("\nNo issues found.")

    if lang in ("rust", "rs") and issues:
        lines.append("\nRust auto-fix is OFF — review issues and apply manually.")

    # Always push to canvas — fixed code if available, original if clean
    push_code = fixed if (auto and fixed) else original
    if push_code:
        if auto and fixed:
            lines.append("\nFixed code pushed to debug tab.")
        else:
            lines.append("\nCode pushed to debug tab.")
        import os as _os
        fname = _os.path.basename(result.get("filepath", "WormBot"))
        note = result.get("_status_note", "")
        if note:
            lines.append(f"\n{note}")
        lines.append(f"[DEBUG:{fname}:{lang}: {push_code}]")

    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────

def _detect_language(code):
    import re
    c = code.lower().strip()
    if c.startswith('<!doctype') or '<html' in c:
        return 'html'
    if re.search(r'\bfn\s+\w+\s*\(', code):
        return 'rust'
    if re.search(r'\bdef\s+\w+\s*\(', code):
        return 'python'
    if re.search(r'\bfunction\b|\bconst\b|\blet\b|\bvar\b', code):
        return 'javascript'
    if c.strip().startswith('{') or c.strip().startswith('['):
        return 'json'
    return 'python'


def _log_activity(action, lang, result):
    _report_log.append({
        "action":     action,
        "lang":       lang,
        "status":     result.get("status", "unknown"),
        "issues":     len(result.get("issues", [])),
        "auto_fixed": result.get("auto_fixed", False),
        "time":       datetime.now().strftime("%H:%M:%S")
    })
    if len(_report_log) > 100:
        _report_log.pop(0)
