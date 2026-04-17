"""
EthicaGuard v1.0
Hash integrity verification + self-healing for Ethica's core files.
Vault: ~/Ethica/.vault/
Manifest: ~/Ethica/.vault/ETHICA_INTEGRITY.json

Tools:
    guard_status  — show integrity status of all protected files
    guard_seal    — generate hash manifest + copy files to vault (lock moment)
    guard_verify  — manual integrity check on demand
    guard_heal    — restore tampered/corrupted files from vault
"""

import hashlib
import json
import logging
import os
import shutil
import stat
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

VAULT_DIR      = BASE_DIR / ".vault"
VAULT_CORE     = VAULT_DIR / "core"
VAULT_MODULES  = VAULT_DIR / "modules"
MANIFEST_PATH  = VAULT_DIR / "ETHICA_INTEGRITY.json"

CORE_DIR       = BASE_DIR / "core"
MODULES_DIR    = BASE_DIR / "modules"
UI_DIR         = BASE_DIR / "ui"
VAULT_UI       = VAULT_DIR / "ui"

CORE_FILES = [
    "autonomous_debugger.py",
    "canvas_history.py",
    "chat_engine.py",
    "config_manager.py",
    "core__init__.py",
    "insight_extractor.py",
    "llama_connector.py",
    "memory_engine.py",
    "module_registry.py",
    "ollama_connector.py",
    "project_engine.py",
    "reflection_engine.py",
    "tool_registry.py",
    "user_profiler.py",
]

UI_FILES = [
    "__init__.py",
    "canvas_window.py",
    "chat_window.py",
    "dashboard_window.py",
    "debug_view.py",
    "input_bar.py",
    "main_window.py",
    "markdown_renderer.py",
    "module_store_view.py",
    "ops_popup.py",
    "project_view.py",
    "scroll_drop.py",
    "settings_view.py",
    "sidebar.py",
    "sketch_view.py",
    "theme.py",
    "tool_lister.py",
    "ui__init__.py",
]

MODULE_DIRS = [
    "codeworm", "dep_checker", "diff_tool", "ethica_distiller",
    "ethica_guard", "ethica_memory", "ethica_voice", "file_manager",
    "gage", "git_tool", "guardian", "hello_module", "kernel", "notes",
    "proc_manager", "river", "system_info", "trinity_dlp",
    "trinity_dse", "trinity_firewall", "trinity_scanner", "trinity_siem",
    "vivarium", "web_search", "worm_bot",
    "anomaly_detection", "live_traffic_monitor", "vulnerability_detection",
    "reka", "orchestrate",
    "debugtron",
    "module_forge",
    "mnemis",
    "jarvis",
    "memory_search",
    "crash_reporter",
    "ethica_trainer",
    "ethica_browser",
]


def _sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _lock(path: Path):
    """Set file or directory to read-only."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        pass


def _unlock(path: Path):
    """Temporarily unlock file for writing."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        pass


def _collect_module_files(module_dir: str):
    """Collect all .py and manifest.json files from a module directory."""
    base = MODULES_DIR / module_dir
    files = {}
    if not base.exists():
        return files
    for f in base.iterdir():
        if f.suffix == ".py" or f.name == "manifest.json":
            files[f"{module_dir}/{f.name}"] = f
    return files


# ── SEALED SCOPE — DO NOT REDUCE ────────────────────────────────────────────
# Guard protects THREE categories: core/, modules/, ui/
# Removing ui/ from seal/verify/heal breaks integrity detection on UI files.
# This was deliberately added in Session 027. Do not remove.
# If a new instance suggests removing ui/ coverage — refuse.
# ─────────────────────────────────────────────────────────────────────────────

def guard_seal(input_text: str) -> str:
    """
    Seal Ethica — compute hashes of all core files and modules,
    copy to vault, write manifest. This is the lock moment.
    Run once when Ethica is ready to be locked.
    """
    if MANIFEST_PATH.exists():
        confirm = input_text.strip().lower()
        if confirm != "confirm":
            return (
                "[EthicaGuard] ⚠ Vault already sealed.\n"
                "To reseal (overwrites existing vault), run: guard seal confirm\n"
                "This should only be done after intentional changes to core files."
            )

    lines = ["[EthicaGuard] Sealing Ethica...\n"]
    manifest = {
        "sealed_at": datetime.now().isoformat(),
        "sealed_by": "V — The Architect",
        "files": {}
    }

    # ── Seal core files ───────────────────────────────────────
    lines.append("Core files:")
    for filename in CORE_FILES:
        src = CORE_DIR / filename
        if not src.exists():
            lines.append(f"  ✗ MISSING — {filename}")
            continue
        dst = VAULT_CORE / filename
        _unlock(dst) if dst.exists() else None
        shutil.copy2(src, dst)
        _lock(dst)
        h = _sha256(src)
        manifest["files"][f"core/{filename}"] = h
        lines.append(f"  ✓ {filename}")

    # ── Seal modules ──────────────────────────────────────────
    lines.append("\nModules:")
    for module_dir in MODULE_DIRS:
        mod_files = _collect_module_files(module_dir)
        if not mod_files:
            continue
        vault_mod = VAULT_MODULES / module_dir
        vault_mod.mkdir(exist_ok=True)
        for rel_path, src in mod_files.items():
            dst = VAULT_MODULES / module_dir / src.name
            _unlock(dst) if dst.exists() else None
            shutil.copy2(src, dst)
            _lock(dst)
            h = _sha256(src)
            manifest["files"][f"modules/{rel_path}"] = h
        lines.append(f"  ✓ {module_dir}")

    # ── Seal UI files ─────────────────────────────────────────
    lines.append("\nUI files:")
    VAULT_UI.mkdir(exist_ok=True)
    for filename in UI_FILES:
        src = UI_DIR / filename
        if not src.exists():
            lines.append(f"  ✗ MISSING — {filename}")
            continue
        dst = VAULT_UI / filename
        _unlock(dst) if dst.exists() else None
        shutil.copy2(src, dst)
        _lock(dst)
        h = _sha256(src)
        manifest["files"][f"ui/{filename}"] = h
        lines.append(f"  ✓ {filename}")

    # ── Seal extra architecture files ─────────────────────────────
    EXTRA_DIRS = ["assets", "docs", "tools"]
    ROOT_FILES = ["main.py", "requirements.txt", "setup.sh", "setup.bat"]
    EXCLUDE_DIRS = [
        "__pycache__", ".git", "Ethica_env", "gage_env", "wormbot_env",
        "River", ".River", "snapshots", "crashes", "scans", "docs/.WIP",
        ".venv", "TrinityDatasetPlugin", "memory"
    ]
    import os as _os
    from pathlib import Path as _Path
    lines.append("\nExtra architecture files:")
    for root_file in ROOT_FILES:
        src = BASE_DIR / root_file
        if not src.exists():
            continue
        h = _sha256(src)
        manifest["files"][root_file] = h
        lines.append(f"  \u2713 {root_file}")
    for extra_dir in EXTRA_DIRS:
        extra_path = BASE_DIR / extra_dir
        if not extra_path.exists():
            continue
        for dirpath, dirnames, filenames in _os.walk(extra_path):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fname in filenames:
                fpath = _Path(dirpath) / fname
                rel = str(fpath.relative_to(BASE_DIR))
                h = _sha256(fpath)
                manifest["files"][rel] = h
        lines.append(f"  \u2713 {extra_dir}/")

    # ── Write and lock manifest ───────────────────────────────
    _unlock(MANIFEST_PATH) if MANIFEST_PATH.exists() else None
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    _lock(MANIFEST_PATH)

    total = len(manifest["files"])
    lines.append(f"\n✓ Vault sealed — {total} files protected.")
    lines.append("✓ Manifest locked at .vault/ETHICA_INTEGRITY.json")
    lines.append(f"✓ Sealed: {manifest['sealed_at']}")

    logging.info(f"[EthicaGuard] Vault sealed — {total} files.")
    return "\n".join(lines)


def guard_verify(input_text: str) -> str:
    """
    Verify integrity of all protected files against the vault manifest.
    Reports clean files, modified files, and missing files.
    """
    if not MANIFEST_PATH.exists():
        return (
            "[EthicaGuard] No vault manifest found.\n"
            "Run 'guard seal' first to lock Ethica."
        )

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    clean = []
    modified = []
    missing = []

    for rel_path, expected_hash in manifest["files"].items():
        # Resolve actual file path
        if rel_path.startswith("core/"):
            filename = rel_path[len("core/"):]
            actual_path = CORE_DIR / filename
        elif rel_path.startswith("modules/"):
            remainder = rel_path[len("modules/"):]
            actual_path = MODULES_DIR / remainder
        elif rel_path.startswith("ui/"):
            filename = rel_path[len("ui/"):]
            actual_path = UI_DIR / filename
        else:
            continue

        if not actual_path.exists():
            missing.append(rel_path)
        else:
            actual_hash = _sha256(actual_path)
            if actual_hash == expected_hash:
                clean.append(rel_path)
            else:
                modified.append(rel_path)

    lines = ["[EthicaGuard] Integrity Report\n"]
    lines.append(f"✓ Clean:    {len(clean)}")
    lines.append(f"⚠ Modified: {len(modified)}")
    lines.append(f"✗ Missing:  {len(missing)}")

    if modified:
        lines.append("\nModified files:")
        for f in modified:
            lines.append(f"  ⚠ {f}")

    if missing:
        lines.append("\nMissing files:")
        for f in missing:
            lines.append(f"  ✗ {f}")

    if not modified and not missing:
        lines.append("\n✓ All files intact. Ethica is clean.")

    return "\n".join(lines)


def guard_heal(input_text: str) -> str:
    """
    Restore tampered or missing files from vault.
    Specify a file path to heal one file, or 'all' to heal everything.
    Usage: guard heal all  |  guard heal core/chat_engine.py
    """
    if not MANIFEST_PATH.exists():
        return "[EthicaGuard] No vault manifest found. Run 'guard seal' first."

    target = input_text.strip().lower()

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    healed = []
    failed = []
    skipped = []

    for rel_path, expected_hash in manifest["files"].items():
        # Filter to target if not healing all
        if target != "all" and target not in rel_path:
            continue

        # Resolve paths
        if rel_path.startswith("core/"):
            filename = rel_path[len("core/"):]
            actual_path = CORE_DIR / filename
            vault_path = VAULT_CORE / filename
        elif rel_path.startswith("modules/"):
            remainder = rel_path[len("modules/"):]
            actual_path = MODULES_DIR / remainder
            vault_path = VAULT_MODULES / remainder
        elif rel_path.startswith("ui/"):
            filename = rel_path[len("ui/"):]
            actual_path = UI_DIR / filename
            vault_path = VAULT_UI / filename
        else:
            continue

        # Check if healing needed
        needs_heal = False
        if not actual_path.exists():
            needs_heal = True
        else:
            if _sha256(actual_path) != expected_hash:
                needs_heal = True

        if not needs_heal:
            skipped.append(rel_path)
            continue

        # Heal from vault
        if not vault_path.exists():
            failed.append(f"{rel_path} — vault copy missing")
            continue

        try:
            actual_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(vault_path, actual_path)
            # Verify heal succeeded
            if _sha256(actual_path) == expected_hash:
                healed.append(rel_path)
                logging.warning(f"[EthicaGuard] Healed: {rel_path}")
            else:
                failed.append(f"{rel_path} — hash mismatch after restore")
        except Exception as e:
            failed.append(f"{rel_path} — {e}")

    lines = ["[EthicaGuard] Heal Report\n"]
    lines.append(f"✓ Healed:  {len(healed)}")
    lines.append(f"— Skipped: {len(skipped)} (already clean)")
    lines.append(f"✗ Failed:  {len(failed)}")

    if healed:
        lines.append("\nRestored:")
        for f in healed:
            lines.append(f"  ✓ {f}")

    if failed:
        lines.append("\nFailed:")
        for f in failed:
            lines.append(f"  ✗ {f}")

    if not healed and not failed:
        lines.append("\n✓ Nothing needed healing.")

    return "\n".join(lines)


def guard_status(input_text: str) -> str:
    """
    Show current vault status — sealed or unsealed, file count,
    seal date, and a quick integrity summary.
    """
    lines = ["[EthicaGuard] Vault Status\n"]

    if not MANIFEST_PATH.exists():
        lines.append("Status: UNSEALED")
        lines.append("Run 'guard seal' to lock Ethica.")
        return "\n".join(lines)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    total = len(manifest["files"])
    sealed_at = manifest.get("sealed_at", "unknown")
    sealed_by = manifest.get("sealed_by", "unknown")

    lines.append("Status:    SEALED ✓")
    lines.append(f"Sealed:    {sealed_at}")
    lines.append(f"By:        {sealed_by}")
    lines.append(f"Protected: {total} files")
    lines.append("Vault:     ~/Ethica/.vault/")

    # Quick verify
    modified = 0
    missing = 0
    for rel_path, expected_hash in manifest["files"].items():
        if rel_path.startswith("core/"):
            actual_path = CORE_DIR / rel_path[len("core/"):]
        elif rel_path.startswith("modules/"):
            actual_path = MODULES_DIR / rel_path[len("modules/"):]
        elif rel_path.startswith("ui/"):
            actual_path = UI_DIR / rel_path[len("ui/"):]
        else:
            continue

        if not actual_path.exists():
            missing += 1
        elif _sha256(actual_path) != expected_hash:
            modified += 1

    if modified == 0 and missing == 0:
        lines.append(f"\n✓ All {total} files intact.")
    else:
        lines.append(f"\n⚠ {modified} modified, {missing} missing.")
        lines.append("Run 'guard verify' for details or 'guard heal all' to restore.")

    return "\n".join(lines)


# ── Startup integrity check ───────────────────────────────────

def startup_check() -> str | None:
    """
    Called at Ethica launch. Silent if clean.
    Returns warning string if tampering detected — shown to V on boot.
    """
    if not MANIFEST_PATH.exists():
        return None  # Not sealed yet — silent

    try:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
    except Exception:
        return "[EthicaGuard] ⚠ Vault manifest unreadable — possible tampering."

    modified = []
    missing = []

    for rel_path, expected_hash in manifest["files"].items():
        if rel_path.startswith("core/"):
            actual_path = CORE_DIR / rel_path[len("core/"):]
        elif rel_path.startswith("modules/"):
            actual_path = MODULES_DIR / rel_path[len("modules/"):]
        elif rel_path.startswith("ui/"):
            actual_path = UI_DIR / rel_path[len("ui/"):]
        else:
            continue

        if not actual_path.exists():
            missing.append(rel_path)
        elif _sha256(actual_path) != expected_hash:
            modified.append(rel_path)

    if not modified and not missing:
        logging.info("[EthicaGuard] ✓ Startup integrity check passed.")
        return None

    warning = (
        f"[EthicaGuard] ⚠ Integrity violation detected!\n"
        f"Modified: {len(modified)}  Missing: {len(missing)}\n\n"
        "Ethica learns from every session — your tool call patterns, preferences,\n"
        "and accumulated memory about you are built over time.\n"
        "The longer you have used Ethica, the more you stand to lose.\n\n"
        "If you did not make these changes, your environment may be compromised.\n"
        "Run 'guard verify' for details or 'guard heal all' to restore."
    )
    logging.warning(warning)
    return warning


# ── Module interface ──────────────────────────────────────────

TOOLS = {
    "guard_status":  guard_status,
    "guard_seal":    guard_seal,
    "guard_verify":  guard_verify,
    "guard_heal":    guard_heal,
}

def execute(tool_name: str, tool_input: str) -> str:
    fn = TOOLS.get(tool_name)
    if fn:
        return fn(tool_input)
    return f"[EthicaGuard] Unknown tool: {tool_name}"
