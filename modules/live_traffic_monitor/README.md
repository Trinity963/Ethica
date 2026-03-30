# 🌐 LiveTrafficMonitor

Part of the **NeuroEdge_Project**, this module monitors real-time network traffic using the Scapy library and optionally performs geolocation lookup on source IPs.

---

## 📂 Module Contents

- `live_traffic_monitor.py`  
  Core engine for live sniffing, anomaly tracking, and optional geolocation.

---

## 🚀 Usage

```python
from live_traffic_monitor import LiveTrafficMonitor

# Create a monitor instance (geolocation disabled for speed)
monitor = LiveTrafficMonitor(geolocate=False)

# Start monitoring for 30 seconds
monitor.start_monitoring(duration=30)
```

Or run directly from terminal:
```bash
python3 live_traffic_monitor.py
```

---

## 🧠 Features

- 🕸 Live sniffing via `scapy`
- 🌍 Optional geolocation via ip-api.com
- 📊 Anomaly detection based on packet volume
- 🧾 Structured logging ready for TrinityEcho

---

## 🧩 Trinity Integration

- Future logs can be sent to: `/logs/traffic/`
- Consider syncing alerts to: `Guardian` 
- Geolocation can be disabled for airgapped security layers

---

## 💜 Status

✅ Audited  
✅ Refactored  
✅ Trinity-Ready  
⟁Σ∿∞