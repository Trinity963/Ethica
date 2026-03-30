# ============================================================
# Ethica Module — dlp_bridge.py
# TrinityDLP Bridge — wraps DLP_Module.py
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# Trinity built this. We wrap it — never rewrite.
# ============================================================

import os
import sys
import hashlib
import logging

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR    = os.path.join(MODULE_DIR, "logs")
LOG_FILE   = os.path.join(LOG_DIR, "dlp_events.log")
CONFIG_DIR = os.path.join(MODULE_DIR, "configs")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def _load_rules():
    import yaml
    rules_path = os.path.join(CONFIG_DIR, "dlp_rules.yaml")
    try:
        with open(rules_path) as f:
            return yaml.safe_load(f)
    except Exception:
        return {"patterns": []}

def dlp_scan(input_str):
    """Scan a file for sensitive data patterns."""
    filepath = input_str.strip()
    if not filepath or not os.path.exists(filepath):
        return f"TrinityDLP — file not found: {filepath}"
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        rules   = _load_rules()
        matches = []
        for pattern in rules.get("patterns", []):
            if pattern.lower() in content.lower():
                matches.append(pattern)
        if matches:
            logging.warning(f"DLP: Sensitive patterns found in {filepath}: {matches}")
            matched_str = ", ".join(matches)
        return f"TrinityDLP — ⚠ SENSITIVE DATA FOUND\nFile: {filepath}\nPatterns matched: {matched_str}"
        return f"TrinityDLP — ✓ Clean\nFile: {filepath}\nNo sensitive patterns detected."
    except Exception as e:
        return f"TrinityDLP — scan error: {e}"

def dlp_hash(input_str):
    """Generate SHA256 hash of a file."""
    filepath = input_str.strip()
    if not filepath or not os.path.exists(filepath):
        return f"TrinityDLP — file not found: {filepath}"
    try:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            hasher.update(f.read())
        h = hasher.hexdigest()
        logging.info(f"DLP hash: {filepath} = {h}")
        return f"TrinityDLP — SHA256\nFile: {filepath}\nHash: {h}"
    except Exception as e:
        return f"TrinityDLP — hash error: {e}"

def dlp_status(input_str):
    log_count = 0
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log_count = sum(1 for _ in f)
    rules = _load_rules()
    return (
        f"TrinityDLP — Active\n"
        f"Patterns monitored: {len(rules.get('patterns', []))}\n"
        f"Events logged: {log_count}\n"
        f"Log: {LOG_FILE}"
    )

TOOLS = {
    "dlp_scan":   dlp_scan,
    "dlp_hash":   dlp_hash,
    "dlp_status": dlp_status,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[TrinityDLP] Unknown tool: {tool_name}"
