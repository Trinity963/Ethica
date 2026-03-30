"""
LiveTrafficMonitor bridge — Ethica module
Tools: traffic_start, traffic_status, traffic_anomalies
"""
import sys
import json
import subprocess
import os
import datetime

WORKER       = os.path.join(os.path.dirname(__file__), "_traffic_worker.py")
GAGE_PYTHON  = os.path.expanduser("~/Ethica/modules/gage/gage_env/bin/python")
STATUS_FILE  = os.path.expanduser("~/Ethica/status/traffic_status.json")

def _write_status(state, task, action, result=None):
    data = {
        "module": "LiveTrafficMonitor",
        "state": state,
        "current_task": task,
        "last_action": action,
        "last_result": result or {},
        "updated": datetime.datetime.now().isoformat()
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def traffic_start(args=""):
    """Start live traffic monitoring. Usage: traffic start [seconds]"""
    _write_status("ACTIVE", "Monitoring traffic", "traffic_start")
    try:
        duration = 15
        if args.strip().isdigit():
            duration = int(args.strip())

        worker_args = json.dumps({"duration": duration, "geolocate": False, "threshold": 50})
        proc = subprocess.run(
            [GAGE_PYTHON, WORKER, worker_args],
            capture_output=True, text=True, timeout=duration + 10
        )

        if proc.returncode != 0:
            err = proc.stderr.strip().splitlines()[-1] if proc.stderr else "unknown error"
            _write_status("IDLE", "Monitor error", err)
            return f"✗ traffic_start error: {err}"

        result = json.loads(proc.stdout.strip())
        total    = sum(result["packet_counts"].values())
        anomaly_count = len(result["anomalies"])
        top = sorted(result["packet_counts"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_str = "\n".join(f"  {ip}: {c} packets" for ip, c in top)

        summary = (
            f"✓ Traffic monitor complete ({duration}s)\n"
            f"Total packets: {total} | Anomalies: {anomaly_count}\n"
            f"Top sources:\n{top_str}"
        )
        _write_status("IDLE", "Monitor complete", "traffic_start", result)
        return summary

    except subprocess.TimeoutExpired:
        _write_status("IDLE", "Monitor timeout", "traffic_start")
        return "✗ traffic_start timed out"
    except Exception as e:
        _write_status("IDLE", "Monitor error", str(e))
        return f"✗ traffic_start error: {e}"

def traffic_status(args=""):
    """Show last traffic monitoring results."""
    try:
        with open(STATUS_FILE) as f:
            data = json.load(f)
        result  = data.get("last_result", {})
        task    = data.get("current_task", "—")
        updated = data.get("updated", "—")
        total   = sum(result.get("packet_counts", {}).values())
        anomaly_count = len(result.get("anomalies", []))
        return (
            f"LiveTrafficMonitor — {task}\n"
            f"Updated: {updated}\n"
            f"Total packets: {total} | Anomalies flagged: {anomaly_count}"
        )
    except FileNotFoundError:
        return "LiveTrafficMonitor — no scan run yet. Try: traffic start"
    except Exception as e:
        return f"✗ traffic_status error: {e}"

def traffic_anomalies(args=""):
    """Show anomalous IPs from last traffic scan."""
    try:
        with open(STATUS_FILE) as f:
            data = json.load(f)
        result    = data.get("last_result", {})
        anomalies = result.get("anomalies", [])
        threshold = result.get("threshold", 50)
        updated   = data.get("updated", "—")

        if not anomalies:
            return f"✓ No anomalies detected in last scan (threshold: {threshold} packets) @ {updated}"

        lines = "\n".join(f"  ⚠ {a['ip']} — {a['count']} packets" for a in anomalies)
        return (
            f"Traffic anomalies (threshold: {threshold}) @ {updated}\n"
            f"{lines}"
        )
    except FileNotFoundError:
        return "LiveTrafficMonitor — no scan run yet. Try: traffic start"
    except Exception as e:
        return f"✗ traffic_anomalies error: {e}"
