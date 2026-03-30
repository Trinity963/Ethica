# ============================================================
# Ethica Module — anomaly_bridge.py
# AnomalyDetection — Isolation Forest anomaly detection
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# anomaly_scan   — detect anomalies in data
# anomaly_train  — train model on baseline data
# anomaly_status — model state
# ============================================================

import os
import sys
import json
import subprocess
from pathlib import Path

MODULE_DIR  = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR    = MODULE_DIR.parent.parent
WORKER      = str(MODULE_DIR / "_anomaly_worker.py")
GAGE_PYTHON  = str(BASE_DIR / "modules" / "gage" / "gage_env" / "bin" / "python")
STATUS_FILE  = BASE_DIR / "status" / "anomaly_status.json"


def _run_worker(command, data=""):
    """Run anomaly worker in gage_env subprocess."""
    try:
        args = [GAGE_PYTHON, WORKER, command]
        if data:
            args.append(data)
        result = subprocess.run(
            args,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None, f"Worker error:\n{result.stderr.strip()}"
        return json.loads(result.stdout.strip()), None
    except subprocess.TimeoutExpired:
        return None, "AnomalyDetection — timed out."
    except Exception as e:
        return None, f"AnomalyDetection — error: {e}"


def anomaly_status(input_str):
    data, err = _run_worker("status")
    if err:
        return err
    trained = data.get("model_trained", False)
    # ── Write status file for dashboard ───────────────────
    try:
        existing = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {}
        existing["model_trained"] = trained
        existing["model_path"] = data.get("model_path", "unknown")
        STATUS_FILE.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass
    return (
        f"AnomalyDetection — Status\n"
        f"Model trained: {'✓ Yes' if trained else '✗ No — run anomaly train <data>'}\n"
        f"Model path: {data.get('model_path', 'unknown')}"
    )


def anomaly_train(input_str):
    raw = input_str.strip()
    if not raw:
        return "AnomalyDetection — usage: anomaly train <comma-separated values or /path/to/file>"
    data, err = _run_worker("train", raw)
    if err:
        return err
    if "error" in data:
        return f"AnomalyDetection — train error: {data['error']}"
    return (
        f"AnomalyDetection — Model trained ✓\n"
        f"Samples used: {data.get('samples', '?')}\n"
        f"Model saved to status/anomaly_model.pkl"
    )


def anomaly_scan(input_str):
    raw = input_str.strip()
    if not raw:
        return "AnomalyDetection — usage: anomaly scan <comma-separated values or /path/to/file>"
    data, err = _run_worker("scan", raw)
    if err:
        return err
    if "error" in data:
        return f"AnomalyDetection — scan error: {data['error']}"

    results = data.get("results", [])
    total = data.get("total", 0)
    anomalies = data.get("anomalies", 0)

    lines = [
        f"AnomalyDetection — Scan Results",
        f"Total samples: {total} | Anomalies: {anomalies}",
        "─" * 40,
    ]
    for r in results:
        flag = "🔴 ANOMALY" if r["label"] == "ANOMALY" else "🟢 normal"
        lines.append(f"  {r['value']:>10.1f}  {flag}")

    # ── Write status file for dashboard ───────────────────
    try:
        from datetime import datetime
        existing = json.loads(STATUS_FILE.read_text()) if STATUS_FILE.exists() else {}
        existing["last_scan"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing["total"] = total
        existing["anomalies"] = anomalies
        STATUS_FILE.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass

    return "\n".join(lines)
