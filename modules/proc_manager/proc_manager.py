# ============================================================
# Ethica v0.1 — proc_manager.py
# Process Manager Module — list, inspect, kill processes
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

import psutil
from datetime import datetime
from pathlib import Path

MODULE_DIR = Path(__file__).parent


# ── Tool: proc_list ───────────────────────────────────────────
def proc_list(input_str):
    """List running processes. Optional filter by name substring."""
    filter_str = input_str.strip().lower() if input_str.strip() else ""

    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'username']):
            try:
                info = p.info
                name = info['name'] or ""
                if filter_str and filter_str not in name.lower():
                    continue
                mem_mb = round(info['memory_info'].rss / 1024 / 1024, 1) if info['memory_info'] else 0.0
                procs.append((info['pid'], name, info['status'], mem_mb, info['username'] or ""))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not procs:
            label = f" matching '{filter_str}'" if filter_str else ""
            return f"ProcessManager — no processes found{label}"

        procs.sort(key=lambda x: x[3], reverse=True)  # sort by memory desc

        header = f"{'PID':<8} {'NAME':<28} {'STATUS':<12} {'MEM MB':<10} {'USER'}\n"
        header += "─" * 70 + "\n"
        rows = ""
        for pid, name, status, mem, user in procs[:50]:
            rows += f"{pid:<8} {name[:27]:<28} {status:<12} {mem:<10} {user}\n"

        count = len(procs)
        label = f" (filter: '{filter_str}')" if filter_str else ""
        summary = f"ProcessManager — {count} process(es){label}\n{'─'*40}\n"
        return summary + header + rows.rstrip()

    except Exception as e:
        return f"ProcessManager — proc_list error: {e}"


# ── Tool: proc_kill ───────────────────────────────────────────
def proc_kill(input_str):
    """Kill a process by PID or name. Input: PID or process name."""
    target = input_str.strip()
    if not target:
        return "ProcessManager — usage: kill process <PID or name>"

    killed = []
    errors = []

    # Try numeric PID first
    if target.isdigit():
        pid = int(target)
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            p.wait(timeout=3)
            killed.append(f"PID {pid} ({name})")
        except psutil.NoSuchProcess:
            return f"ProcessManager — no process with PID {pid}"
        except psutil.AccessDenied:
            return f"ProcessManager — access denied: PID {pid}"
        except psutil.TimeoutExpired:
            try:
                p.kill()
                killed.append(f"PID {pid} ({name}) [force killed]")
            except Exception as e:
                errors.append(f"PID {pid}: {e}")
    else:
        # Kill by name — may match multiple
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if p.info['name'] and target.lower() in p.info['name'].lower():
                    pid = p.info['pid']
                    name = p.info['name']
                    p.terminate()
                    killed.append(f"PID {pid} ({name})")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                errors.append(f"{p.pid}: {e}")

        if not killed and not errors:
            return f"ProcessManager — no process found matching '{target}'"

    lines = [f"ProcessManager — kill '{target}'", "─" * 40]
    if killed:
        lines += [f"✓ Terminated: {k}" for k in killed]
    if errors:
        lines += [f"✗ Error: {e}" for e in errors]
    return "\n".join(lines)


# ── Tool: proc_info ───────────────────────────────────────────
def proc_info(input_str):
    """Detailed info on a process by PID."""
    target = input_str.strip()
    if not target or not target.isdigit():
        return "ProcessManager — usage: process info <PID>"

    pid = int(target)
    try:
        p = psutil.Process(pid)
        with p.oneshot():
            name       = p.name()
            status     = p.status()
            username   = p.username()
            created    = datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
            cpu        = p.cpu_percent(interval=0.1)
            mem        = p.memory_info()
            mem_rss    = round(mem.rss / 1024 / 1024, 2)
            mem_vms    = round(mem.vms / 1024 / 1024, 2)
            try:
                cmdline = " ".join(p.cmdline()) or "[no cmdline]"
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cmdline = "[access denied]"
            try:
                cwd = p.cwd()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cwd = "[access denied]"
            try:
                num_threads = p.num_threads()
            except Exception:
                num_threads = "?"
            try:
                connections = len(p.connections())
            except Exception:
                connections = "?"

        lines = [
            f"ProcessManager — PID {pid}",
            "─" * 40,
            f"Name        : {name}",
            f"Status      : {status}",
            f"User        : {username}",
            f"Started     : {created}",
            f"CPU %       : {cpu}",
            f"RAM RSS     : {mem_rss} MB",
            f"RAM VMS     : {mem_vms} MB",
            f"Threads     : {num_threads}",
            f"Connections : {connections}",
            f"CWD         : {cwd}",
            f"Cmdline     : {cmdline[:120]}",
        ]
        return "\n".join(lines)

    except psutil.NoSuchProcess:
        return f"ProcessManager — no process with PID {pid}"
    except psutil.AccessDenied:
        return f"ProcessManager — access denied: PID {pid}"
    except Exception as e:
        return f"ProcessManager — proc_info error: {e}"


# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "proc_list": proc_list,
    "proc_kill": proc_kill,
    "proc_info": proc_info,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[ProcessManager] Unknown tool: {tool_name}"
