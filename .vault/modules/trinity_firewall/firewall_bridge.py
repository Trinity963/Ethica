# ============================================================
# Ethica Module — firewall_bridge.py
# TrinityFirewall Bridge — wraps TrinityAI_Firewall.py
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Trinity built this. We wrap it — never rewrite.
# Requires scapy for live packet sniffing.
# Requires root/sudo for network interface access.
# ============================================================

import os
import sys
import json
import threading

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(MODULE_DIR, "configs")
LOG_DIR    = os.path.join(MODULE_DIR, "logs")
POLICIES   = os.path.join(CONFIG_DIR, "firewall_policies.json")
LOG_FILE   = os.path.join(LOG_DIR,    "firewall.log")

# Patch hardcoded paths in TrinityAI_Firewall before import
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# ── Firewall state ────────────────────────────────────────────
_firewall_thread  = None
_firewall_running = False
FIREWALL_STATUS_FILE = os.path.expanduser("~/Ethica/status/firewall_status.json")
_firewall_module  = None


def _load_policies():
    try:
        with open(POLICIES, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"blocked_ips": [], "error": str(e)}

def _save_policies(data):
    try:
        with open(POLICIES, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False


# ── Tool: firewall_start ──────────────────────────────────────

def firewall_start(input_str):
    global _firewall_thread, _firewall_running, _firewall_module

    if _firewall_running:
        return "TrinityFirewall — already running."

    try:
        import scapy.all as scapy
    except ImportError:
        return "TrinityFirewall — scapy not installed. Run: pip install scapy"

    try:
        # Patch paths before importing
        import importlib.util, types

        # Read and patch the firewall source
        src_path = os.path.join(MODULE_DIR, "TrinityAI_Firewall.py")
        with open(src_path, "r") as f:
            src = f.read()

        # Replace hardcoded paths with module-relative paths
        src = src.replace(
            '"/mnt/TrinityAI/security/firewall/logs"',
            repr(LOG_DIR)
        ).replace(
            '"/mnt/TrinityAI/security/firewall/configs/firewall_policies.json"',
            repr(POLICIES)
        )

        # Execute patched source in isolated namespace
        ns = {"__name__": "trinity_firewall_patched"}
        exec(compile(src, src_path, "exec"), ns)

        FirewallModule = ns["FirewallModule"]
        _firewall_module = FirewallModule()

        def _run():
            global _firewall_running
            _firewall_running = True
            try:
                import json as _json
                _json.dump({"state": "ACTIVE"}, open(FIREWALL_STATUS_FILE, "w"), indent=2)
            except Exception:
                pass
            try:
                _firewall_module.start_intrusion_detection()
            except Exception:
                pass
            _firewall_running = False
            try:
                import json as _json
                _json.dump({"state": "IDLE"}, open(FIREWALL_STATUS_FILE, "w"), indent=2)
            except Exception:
                pass

        _firewall_thread = threading.Thread(target=_run, daemon=True)
        _firewall_thread.start()

        return "TrinityFirewall — started. Intrusion detection active. Logs: " + LOG_FILE

    except Exception as e:
        return f"TrinityFirewall — start error: {e}"


# ── Tool: firewall_status ─────────────────────────────────────

def firewall_status(input_str):
    policies = _load_policies()
    blocked  = policies.get("blocked_ips", [])
    running  = "● Running" if _firewall_running else "○ Stopped"

    lines = [
        f"TrinityFirewall — {running}",
        f"Blocked IPs ({len(blocked)}):"
    ]
    for ip in blocked:
        lines.append(f"  • {ip}")

    # Last 5 log lines
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                log_lines = f.readlines()
            if log_lines:
                lines.append(f"\nLog (last 5):")
                for l in log_lines[-5:]:
                    lines.append(f"  {l.strip()}")
        except Exception:
            pass

    return "\n".join(lines)


# ── Tool: firewall_block_ip ───────────────────────────────────

def firewall_block_ip(input_str):
    ip = input_str.strip()
    if not ip:
        return "No IP provided."

    policies = _load_policies()
    blocked  = policies.get("blocked_ips", [])

    if ip in blocked:
        return f"TrinityFirewall — {ip} already blocked."

    blocked.append(ip)
    policies["blocked_ips"] = blocked
    _save_policies(policies)

    # Reload policies in running firewall
    if _firewall_module:
        try:
            _firewall_module.policies = policies
        except Exception:
            pass

    return f"TrinityFirewall — {ip} blocked. Total blocked: {len(blocked)}"


# ── Tool: firewall_unblock_ip ─────────────────────────────────

def firewall_unblock_ip(input_str):
    ip = input_str.strip()
    if not ip:
        return "No IP provided."

    policies = _load_policies()
    blocked  = policies.get("blocked_ips", [])

    if ip not in blocked:
        return f"TrinityFirewall — {ip} not in blocked list."

    blocked.remove(ip)
    policies["blocked_ips"] = blocked
    _save_policies(policies)

    if _firewall_module:
        try:
            _firewall_module.policies = policies
        except Exception:
            pass

    return f"TrinityFirewall — {ip} unblocked. Total blocked: {len(blocked)}"


# ── Tool: firewall_read_log ───────────────────────────────────

def firewall_read_log(input_str):
    try:
        n = int(input_str.strip()) if input_str.strip().isdigit() else 20
    except Exception:
        n = 20

    if not os.path.exists(LOG_FILE):
        return "TrinityFirewall — no log file found."

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        if not lines:
            return "TrinityFirewall — log is empty."
        tail = lines[-n:]
        return f"TrinityFirewall Log (last {n}):\n" + "".join(tail)
    except Exception as e:
        return f"TrinityFirewall — log read error: {e}"


# ── Module registry interface ─────────────────────────────────

TOOLS = {
    "firewall_start":     firewall_start,
    "firewall_status":    firewall_status,
    "firewall_block_ip":  firewall_block_ip,
    "firewall_unblock_ip":firewall_unblock_ip,
    "firewall_read_log":  firewall_read_log,
}

def get_tools():
    return TOOLS

def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    if fn:
        return fn(input_str)
    return f"[TrinityFirewall] Unknown tool: {tool_name}"
