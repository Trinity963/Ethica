"""
LiveTrafficMonitor worker — runs in gage_env (scapy isolated)
Called as subprocess. Writes results to stdout as JSON.
"""
import sys
import json
import time
import os

sys.path.insert(0, os.path.expanduser("~/Ethica/assets/LiveTrafficMonitor"))

from live_traffic_monitor import LiveTrafficMonitor

def main():
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    duration  = int(args.get("duration", 15))
    geolocate = bool(args.get("geolocate", False))
    threshold = int(args.get("threshold", 50))

    monitor = LiveTrafficMonitor(geolocate=geolocate)
    monitor.start_monitoring(duration=duration)

    # Collect results
    anomalies = []
    for ip, count in monitor.packet_count.items():
        if count > threshold:
            anomalies.append({"ip": ip, "count": count})

    result = {
        "packet_counts": dict(monitor.packet_count),
        "anomalies": anomalies,
        "duration": duration,
        "threshold": threshold
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
