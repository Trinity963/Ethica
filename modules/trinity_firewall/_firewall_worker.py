"""
TrinityFirewall worker — runs under cap_net_raw python binary.
Called as subprocess. Requires CAP_NET_RAW capability.
# WORM:SKIP
"""
import sys
import os
import json

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MODULE_DIR)

LOG_DIR  = os.path.join(MODULE_DIR, "logs")
POLICIES = os.path.join(MODULE_DIR, "configs", "firewall_policies.json")
STATUS_FILE = os.path.expanduser("~/Ethica/status/firewall_status.json")
PID_FILE    = os.path.expanduser("~/Ethica/status/firewall_pid.json")

def main():
    src_path = os.path.join(MODULE_DIR, "TrinityAI_Firewall.py")
    with open(src_path, "r") as f:
        src = f.read()

    src = src.replace(
        '"/mnt/TrinityAI/security/firewall/logs"',
        repr(LOG_DIR)
    ).replace(
        '"/mnt/TrinityAI/security/firewall/configs/firewall_policies.json"',
        repr(POLICIES)
    )

    ns = {"__name__": "trinity_firewall_patched", "__file__": src_path}
    exec(compile(src, src_path, "exec"), ns)

    FirewallModule = ns["FirewallModule"]
    module = FirewallModule()

    try:
        json.dump({"pid": os.getpid()}, open(PID_FILE, "w"), indent=2)
    except Exception:
        pass
    try:
        json.dump({"state": "ACTIVE"}, open(STATUS_FILE, "w"), indent=2)
    except Exception:
        pass

    try:
        module.start_intrusion_detection()
    except Exception as e:
        print(f"firewall error: {e}", file=sys.stderr)

    try:
        json.dump({"state": "IDLE"}, open(STATUS_FILE, "w"), indent=2)
    except Exception:
        pass
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass

if __name__ == "__main__":
    main()
