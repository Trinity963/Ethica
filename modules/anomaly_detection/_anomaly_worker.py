# _anomaly_worker.py — runs in gage_env, called by anomaly_bridge.py
import sys
import json
import os
import pickle
import numpy as np

ASSETS_DIR = os.path.expanduser("~/Ethica/assets/AnomalyDetection")
MODEL_PATH = os.path.expanduser("~/Ethica/status/anomaly_model.pkl")

sys.path.insert(0, ASSETS_DIR)

# Suppress print statements from anomaly_detector.py during import
import builtins
_real_print = builtins.print
def _silent_print(*args, **kwargs):
    pass
builtins.print = _silent_print

from anomaly_detector import AnomalyDetector

# Restore print for our own JSON output
builtins.print = _real_print

def load_detector():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return AnomalyDetector(contamination=0.1)

def save_detector(detector):
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(detector, f)

def parse_input(raw):
    """Parse comma-separated floats or a file path into np array."""
    raw = raw.strip()
    if os.path.exists(os.path.expanduser(raw)):
        path = os.path.expanduser(raw)
        with open(path) as f:
            values = [float(x.strip()) for x in f.read().split(",") if x.strip()]
    else:
        values = [float(x.strip()) for x in raw.split(",") if x.strip()]
    return np.array(values).reshape(-1, 1)

if __name__ == "__main__":
    command = sys.argv[1]  # train | scan | status
    data_raw = sys.argv[2] if len(sys.argv) > 2 else ""

    if command == "status":
        exists = os.path.exists(MODEL_PATH)
        print(json.dumps({
            "model_trained": exists,
            "model_path": MODEL_PATH
        }))

    elif command == "train":
        try:
            data = parse_input(data_raw)
            detector = AnomalyDetector(contamination=0.1)
            builtins.print = _silent_print
            detector.train_model(data)
            builtins.print = _real_print
            save_detector(detector)
            print(json.dumps({
                "status": "trained",
                "samples": len(data)
            }))
        except Exception as e:
            print(json.dumps({"error": str(e)}))

    elif command == "scan":
        try:
            detector = load_detector()
            data = parse_input(data_raw)
            builtins.print = _silent_print
            predictions = detector.predict_anomalies(data)
            builtins.print = _real_print
            values = data.flatten().tolist()
            results = []
            for val, pred in zip(values, predictions):
                results.append({
                    "value": val,
                    "label": "ANOMALY" if pred == -1 else "normal"
                })
            anomaly_count = sum(1 for p in predictions if p == -1)
            print(json.dumps({
                "total": len(results),
                "anomalies": anomaly_count,
                "results": results
            }))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
