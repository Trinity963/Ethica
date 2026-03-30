# 🧠 AnomalyDetection Module

Part of the **NeuroEdge_Project**, this module provides a lightweight anomaly detection engine using the Isolation Forest algorithm.  
It is ideal for identifying outliers or suspicious behavior in real-time data streams, such as:

- Network traffic anomalies
- System behavior deviations
- Sensor pattern outliers

---

## 📂 Module Contents

- `anomaly_detector.py`  
  Core class for training and predicting anomalies using Isolation Forest.

---

## 🚀 Usage

```python
from anomaly_detector import AnomalyDetector
import numpy as np

# Create instance
detector = AnomalyDetector(contamination=0.1)

# Train model on normal data
detector.train_model(np.array([[100], [200], [300]]))

# Predict anomalies
new_data = np.array([[100], [5000]])
predictions = detector.predict_anomalies(new_data)
```

---

## 🧩 Integration Path

This module is intended to be integrated with TrinityPrime’s Guardian or CMA layers.
- Logs can be routed to `/logs/security/anomalies.log`
- Add  logging later with `TrinityEcho`
- 

---

## 💜 Status

✅ Audited  
✅ Refactored  
✅ Trinity-Ready (Phase 1)  
⟁Σ∿∞