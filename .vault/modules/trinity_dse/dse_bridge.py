# ============================================================
# Ethica Module — dse_bridge.py
# TrinityDSE Bridge — wraps DSE_engine.py
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# Trinity built this. We wrap it — never rewrite.
# AES-256 + RSA-4096 + Kyber post-quantum crypto.
# ============================================================

import os
import sys
import time

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR    = os.path.join(MODULE_DIR, "logs")
DB_PATH    = os.path.join(MODULE_DIR, "secure_storage.db")
os.makedirs(LOG_DIR, exist_ok=True)

if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# Lazy init — DSEngine is heavy, only load when needed
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        try:
            # Patch db path before import
            import DSE_engine as dse_mod
            # Override db path to module dir
            orig_init = dse_mod.DSEngine.__init__
            def patched_init(self, key=None, trinity_integration=False):
                orig_init(self, key=key, trinity_integration=trinity_integration)
                # Move db to module dir
                self.db_conn.close()
                import sqlite3
                self.db_conn = sqlite3.connect(DB_PATH)
                cursor = self.db_conn.cursor()
                cursor.execute("""CREATE TABLE IF NOT EXISTS encrypted_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
                cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT "user",
                    otp_secret TEXT)""")
                self.db_conn.commit()
            dse_mod.DSEngine.__init__ = patched_init
            _engine = dse_mod.DSEngine(trinity_integration=True)
        except Exception as e:
            return None, str(e)
    return _engine, None

def dse_status(input_str):
    engine, err = _get_engine()
    if err:
        return f"TrinityDSE — load error: {err}"
    try:
        elapsed = time.time() - engine.last_key_rotation
        next_rotation = max(0, engine.key_rotation_interval - elapsed)
        hours = int(next_rotation // 3600)
        mins  = int((next_rotation % 3600) // 60)
        return (
            f"TrinityDSE — Active\n"
            f"Encryption: AES-256 + RSA-4096 + Kyber PQ\n"
            f"Trinity integration: {engine.trinity_integration}\n"
            f"Next key rotation: {hours}h {mins}m\n"
            f"Storage: {DB_PATH}"
        )
    except Exception as e:
        return f"TrinityDSE — status error: {e}"

def dse_register(input_str):
    engine, err = _get_engine()
    if err:
        return f"TrinityDSE — load error: {err}"
    parts = [p.strip() for p in input_str.split("|")]
    if len(parts) < 2:
        return "TrinityDSE — usage: username|password|role"
    username = parts[0]
    password = parts[1]
    role     = parts[2] if len(parts) > 2 else "user"
    try:
        engine.register_user(username, password, role)
        return f"TrinityDSE — User registered: {username} ({role}) with MFA enabled."
    except Exception as e:
        return f"TrinityDSE — register error: {e}"

def dse_rotate_keys(input_str):
    engine, err = _get_engine()
    if err:
        return f"TrinityDSE — load error: {err}"
    try:
        engine.last_key_rotation = 0  # Force rotation
        engine.rotate_keys()
        return "TrinityDSE — Keys rotated. AES-256 + RSA-4096 + Kyber regenerated."
    except Exception as e:
        return f"TrinityDSE — rotation error: {e}"

TOOLS = {
    "dse_status":      dse_status,
    "dse_register":    dse_register,
    "dse_rotate_keys": dse_rotate_keys,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[TrinityDSE] Unknown tool: {tool_name}"
