# ============================================================
# Ethica Module — system_info.py
# SystemInfo — ecosystem heartbeat. Machine awareness.
# Architect: Victory  |  Build Partner: River
# ⟁Σ∿∞
# ============================================================

import psutil
import platform
import os
import subprocess
from datetime import datetime, timedelta


def _fmt_bytes(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _uptime():
    try:
        boot = psutil.boot_time()
        delta = timedelta(seconds=int(datetime.now().timestamp() - boot))
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    except Exception:
        return "unknown"


# ── Tools ──────────────────────────────────────────────────

def sysinfo_status(input_str):
    """
    Full system snapshot — OS, CPU, RAM, disk, uptime, Ollama.
    Input: any string (ignored)
    """
    try:
        cpu_pct   = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True)
        ram       = psutil.virtual_memory()
        disk      = psutil.disk_usage('/')
        uname     = platform.uname()
        uptime    = _uptime()

        # Ollama status
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=3
            )
            ollama_lines = result.stdout.strip().split("\n")
            ollama_models = len([l for l in ollama_lines if l and "NAME" not in l])
            ollama_status = f"✓ {ollama_models} model(s) registered"
        except Exception:
            ollama_status = "⚠ Ollama not reachable"

        lines = [
            "⟁ System Status",
            "─" * 40,
            f"Host:     {uname.node}",
            f"OS:       {uname.system} {uname.release}",
            f"Uptime:   {uptime}",
            "",
            f"CPU:      {cpu_pct:.1f}% — {cpu_count} cores",
            f"RAM:      {_fmt_bytes(ram.used)} / {_fmt_bytes(ram.total)} ({ram.percent:.1f}%)",
            f"Disk:     {_fmt_bytes(disk.used)} / {_fmt_bytes(disk.total)} ({disk.percent:.1f}%)",
            "",
            f"Ollama:   {ollama_status}",
            f"Python:   {platform.python_version()}",
            f"Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ sysinfo_status error: {e}"


def sysinfo_memory(input_str):
    """
    Detailed RAM breakdown — used, available, cached, swap.
    Input: any string (ignored)
    """
    try:
        ram  = psutil.virtual_memory()
        swap = psutil.swap_memory()

        lines = [
            "⟁ Memory",
            "─" * 40,
            f"Total:     {_fmt_bytes(ram.total)}",
            f"Used:      {_fmt_bytes(ram.used)} ({ram.percent:.1f}%)",
            f"Available: {_fmt_bytes(ram.available)}",
            f"Cached:    {_fmt_bytes(getattr(ram, 'cached', 0))}",
            f"Buffers:   {_fmt_bytes(getattr(ram, 'buffers', 0))}",
            "",
            f"Swap Total: {_fmt_bytes(swap.total)}",
            f"Swap Used:  {_fmt_bytes(swap.used)} ({swap.percent:.1f}%)",
            f"Swap Free:  {_fmt_bytes(swap.free)}",
        ]
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ sysinfo_memory error: {e}"


def sysinfo_disk(input_str):
    """
    Disk usage for all mounted partitions.
    Input: any string (ignored)
    """
    try:
        lines = ["⟁ Disk", "─" * 40]
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                lines.append(
                    f"{part.mountpoint:<20} "
                    f"{_fmt_bytes(usage.used):>10} / {_fmt_bytes(usage.total):>10} "
                    f"({usage.percent:.1f}%)"
                )
            except PermissionError:
                lines.append(f"{part.mountpoint:<20} — no access")
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ sysinfo_disk error: {e}"


def sysinfo_procs(input_str):
    """
    Top 10 processes by CPU usage.
    Input: any string (ignored)
    """
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU
        procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        top = procs[:10]

        lines = [
            "⟁ Top Processes",
            "─" * 40,
            f"{'PID':<8} {'NAME':<25} {'CPU%':>6} {'MEM%':>6}",
            "─" * 40,
        ]
        for p in top:
            lines.append(
                f"{str(p.get('pid','?')):<8} "
                f"{str(p.get('name','?'))[:24]:<25} "
                f"{p.get('cpu_percent',0):>6.1f} "
                f"{p.get('memory_percent',0):>6.1f}"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ sysinfo_procs error: {e}"


def sysinfo_network(input_str):
    """
    Network interfaces and IO counters.
    Input: any string (ignored)
    """
    try:
        io = psutil.net_io_counters(pernic=True)
        addrs = psutil.net_if_addrs()

        lines = ["⟁ Network", "─" * 40]
        for iface, stats in io.items():
            addr_list = addrs.get(iface, [])
            ip = next((a.address for a in addr_list
                      if a.family.name == 'AF_INET'), "no IP")
            lines.append(
                f"{iface:<12} {ip:<18} "
                f"↑ {_fmt_bytes(stats.bytes_sent):>10}  "
                f"↓ {_fmt_bytes(stats.bytes_recv):>10}"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ sysinfo_network error: {e}"


# ── Module registry interface ──────────────────────────────

TOOLS = {
    "sysinfo_status":  sysinfo_status,
    "sysinfo_memory":  sysinfo_memory,
    "sysinfo_disk":    sysinfo_disk,
    "sysinfo_procs":   sysinfo_procs,
    "sysinfo_network": sysinfo_network,
}

def get_tools():
    return TOOLS

def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[SystemInfo] Unknown tool: {tool_name}"
