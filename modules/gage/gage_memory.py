# ============================================================
# Ethica v0.1 — gage_memory.py
# Gage Sentinel Memory — wake loader + session distiller
# Architect: Victory  |  Build Partner: River ⟁Σ∿∞
#
# Gage wakes each session already knowing:
#   - Local network topology (dynamic, not hardcoded)
#   - Firewall policies + recent events
#   - DLP policy state + any events
#   - SIEM config + alert thresholds
#   - WormHunter last scan result
#   - Vault integrity snapshot
#
# Three tools:
#   gage_wake         — load telemetry, arm Gage for session
#   gage_distill_run  — harvest session, update gage_build.json
#   gage_status       — show Gage's current operational picture
# ============================================================

import json
import re
import socket
from datetime import datetime
from pathlib import Path

# ── Path resolution ───────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent.parent
MEMORY_DIR  = BASE_DIR / "memory"
MOD_DIR     = BASE_DIR / "modules"

GAGE_BUILD  = MEMORY_DIR / "gage_build.json"
GAGE_STATE  = MEMORY_DIR / "gage_state.json"

FW_LOG      = MOD_DIR / "trinity_firewall" / "logs" / "firewall.log"
FW_POLICY   = MOD_DIR / "trinity_firewall" / "configs" / "firewall_policies.json"
DLP_LOG     = MOD_DIR / "trinity_dlp" / "logs" / "dlp_events.log"
DLP_POLICY  = MOD_DIR / "trinity_dlp" / "configs" / "dlp_policies.json"
SIEM_CFG    = MOD_DIR / "trinity_siem" / "configs" / "siem_config.json"
WORM_LOG    = MOD_DIR / "worm_bot" / "modules" / "codeworm" / "worm_feed.log"
WORM_CFG    = MOD_DIR / "worm_bot" / "worm_bot_config.json"
VAULT_STATE = BASE_DIR / ".vault" / "ETHICA_INTEGRITY.json"


# ── Helpers ───────────────────────────────────────────────────

def _read_json(path):
    try:
        if Path(path).exists():
            return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_json(path, data):
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return True
    except Exception as e:
        return str(e)


def _tail_log(path, n=50):
    try:
        p = Path(path)
        if not p.exists():
            return []
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except Exception:
        return []


def _get_local_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        s.close()
        ips.append(("primary", primary))
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        if not any(ip == host_ip for _, ip in ips):
            ips.append(("hostname", host_ip))
    except Exception:
        pass
    return ips


def _classify_fw_line(line, local_ips):
    local_prefixes = tuple(
        ip.rsplit('.', 1)[0] for _, ip in local_ips
    )
    found = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
    if not found:
        return 'info'
    if 'BLOCK' in line.upper() or 'DENY' in line.upper():
        return 'blocked'
    if all(ip.startswith(local_prefixes) for ip in found):
        return 'local'
    return 'external'


def _parse_worm_last(lines):
    for line in reversed(lines):
        if '[WORM][DONE]' in line:
            return line.strip()
    return None


# ── Tool: gage_wake ───────────────────────────────────────────

def gage_wake(input_str):
    now = datetime.now().isoformat()
    report = ["⟁Σ∿∞ Gage — Sentinel Wake", "─" * 40]

    local_ips = _get_local_ips()
    report.append(f"Network : {', '.join(f'{i}={ip}' for i, ip in local_ips)}")

    fw_policy   = _read_json(FW_POLICY)
    blocked_ips = fw_policy.get("blocked_ips", [])
    report.append(f"Firewall blocked IPs : {len(blocked_ips)} entries")

    fw_lines  = _tail_log(FW_LOG, 100)
    fw_counts = {"local": 0, "blocked": 0, "external": 0, "info": 0}
    for line in fw_lines:
        cls = _classify_fw_line(line, local_ips)
        fw_counts[cls] += 1
    report.append(
        f"Firewall log (last 100) : local={fw_counts['local']} "
        f"external={fw_counts['external']} blocked={fw_counts['blocked']}"
    )
    fw_alert = fw_counts['blocked'] > 0 or fw_counts['external'] > 5
    if fw_alert:
        report.append("  ⚠ Firewall anomaly — review recommended")

    dlp_policy = _read_json(DLP_POLICY)
    dlp_lines  = _tail_log(DLP_LOG, 20)
    dlp_events = len([l for l in dlp_lines if l.strip()])
    report.append(
        f"DLP : policy={dlp_policy.get('policy_name','unknown')} "
        f"events_recent={dlp_events}"
    )

    siem_cfg = _read_json(SIEM_CFG)
    report.append(
        f"SIEM : threshold={siem_cfg.get('alert_threshold','?')} "
        f"interval={siem_cfg.get('monitoring_interval','?')}s "
        f"retention={siem_cfg.get('log_retention_days','?')}d"
    )

    worm_lines = _tail_log(WORM_LOG, 20)
    worm_last  = _parse_worm_last(worm_lines)
    report.append(f"WormHunter last scan : {worm_last or 'no scan found'}")

    vault       = _read_json(VAULT_STATE)
    vault_files   = len(vault.get("files", {}))
    vault_sealed  = vault.get("sealed_at", "unknown")
    vault_by      = vault.get("sealed_by", "unknown")
    report.append(
        f"Vault : {vault_files} files | sealed={vault_sealed} | by={vault_by}"
    )

    build = _read_json(GAGE_BUILD)
    build["last_wake"]         = now
    build["local_ips"]         = local_ips
    build["fw_blocked_ips"]    = blocked_ips
    build["fw_log_summary"]    = fw_counts
    build["fw_alert"]          = fw_alert
    build["dlp_policy"]        = dlp_policy.get("policy_name", "unknown")
    build["dlp_events_recent"] = dlp_events
    build["siem_config"]       = siem_cfg
    build["worm_last_scan"]    = worm_last
    build["vault_snapshot"]    = {
        "files": vault_files, "sealed": vault_sealed, "by": vault_by
    }
    build.setdefault("sessions", []).append({
        "wake": now, "fw_summary": fw_counts,
        "dlp_events": dlp_events, "worm_last": worm_last,
        "vault_files": vault_files
    })
    _write_json(GAGE_BUILD, build)

    report.append("─" * 40)
    report.append("✓ gage_build.json updated — Gage is armed")
    return "\n".join(report)


# ── Tool: gage_distill_run ────────────────────────────────────

def gage_distill_run(input_str):
    now       = datetime.now().isoformat()
    local_ips = _get_local_ips()

    fw_lines  = _tail_log(FW_LOG, 200)
    fw_counts = {"local": 0, "blocked": 0, "external": 0, "info": 0}
    for line in fw_lines:
        fw_counts[_classify_fw_line(line, local_ips)] += 1

    dlp_lines  = _tail_log(DLP_LOG, 50)
    dlp_events = [l.strip() for l in dlp_lines if l.strip()]
    worm_lines = _tail_log(WORM_LOG, 30)
    worm_last  = _parse_worm_last(worm_lines)
    vault      = _read_json(VAULT_STATE)

    threat = "CLEAR"
    if fw_counts['blocked'] > 0:
        threat = "ELEVATED — blocked traffic detected"
    elif fw_counts['external'] > 10:
        threat = "WATCH — external traffic above baseline"
    if dlp_events:
        threat = "ELEVATED — DLP events recorded"

    distill = {
        "timestamp":    now,
        "threat_level": threat,
        "fw_summary":   fw_counts,
        "dlp_events":   dlp_events[-5:] if dlp_events else [],
        "worm_last":    worm_last,
        "vault_files":  len(vault.get("files", {})),
        "vault_sealed": vault.get("sealed_at", "unknown"),
    }

    build = _read_json(GAGE_BUILD)
    sessions = build.get("sessions", [])
    if sessions:
        sessions[-1]["distill"] = distill
    build["sessions"]     = sessions
    build["last_distill"] = now
    _write_json(GAGE_BUILD, build)

    state = {
        "last_updated":       now,
        "threat_level":       threat,
        "fw_blocked_ips":     _read_json(FW_POLICY).get("blocked_ips", []),
        "dlp_events_recent":  len(dlp_events),
        "worm_last_scan":     worm_last,
        "vault_files":        vault.get("vault_files", "unknown"),
        "vault_master":       vault.get("vault_master", "unknown"),
    }
    _write_json(GAGE_STATE, state)

    return "\n".join([
        "⟁Σ∿∞ Gage — Session Distill Complete",
        "─" * 40,
        f"Threat level     : {threat}",
        f"Firewall         : local={fw_counts['local']} external={fw_counts['external']} blocked={fw_counts['blocked']}",
        f"DLP events       : {len(dlp_events)}",
        f"WormHunter       : {worm_last or 'no scan'}",
        f"Vault            : {vault.get('vault_files','?')} files | {vault.get('vault_master','?')}",
        "─" * 40,
        "✓ gage_build.json + gage_state.json updated",
    ])


# ── Tool: gage_status ─────────────────────────────────────────

def gage_status(input_str):
    build = _read_json(GAGE_BUILD)
    state = _read_json(GAGE_STATE)
    if not build:
        return "Gage memory not initialised — run 'gage wake' first."
    return "\n".join([
        "⟁Σ∿∞ Gage — Sentinel Status",
        "─" * 40,
        f"Last wake        : {build.get('last_wake','unknown')}",
        f"Last distill     : {build.get('last_distill','never')}",
        f"Threat level     : {state.get('threat_level','UNKNOWN')}",
        f"Firewall blocked : {len(build.get('fw_blocked_ips',[]))} IPs",
        f"FW alert         : {'⚠ YES' if build.get('fw_alert') else 'clear'}",
        f"DLP events       : {build.get('dlp_events_recent',0)}",
        f"WormHunter       : {build.get('worm_last_scan','no scan')}",
        f"Vault            : {build.get('vault_snapshot',{}).get('files','?')} files",
        f"Sessions logged  : {len(build.get('sessions',[]))}",
    ])


# ── Tool registry ─────────────────────────────────────────────

TOOLS = {
    "gage_wake": {
        "name": "gage_wake",
        "description": "Load all telemetry. Arm Gage for session. Call at session start.",
        "input_schema": {"type": "object", "properties": {"confirm": {"type": "string"}}}
    },
    "gage_distill_run": {
        "name": "gage_distill_run",
        "description": "Harvest session telemetry. Update gage_build + gage_state. Call at session close.",
        "input_schema": {"type": "object", "properties": {"confirm": {"type": "string"}}}
    },
    "gage_status": {
        "name": "gage_status",
        "description": "Show Gage's current operational picture.",
        "input_schema": {"type": "object", "properties": {"confirm": {"type": "string"}}}
    },
}


def get_tools():
    return TOOLS


def execute(tool_name, input_str):
    fn = {
        "gage_wake":        gage_wake,
        "gage_distill_run": gage_distill_run,
        "gage_status":      gage_status,
    }
    if tool_name in fn:
        return fn[tool_name](input_str)
    return f"Unknown tool: {tool_name}"
