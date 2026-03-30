import os
import json
import yaml
import logging
from datetime import datetime

# ==============================
# SIEM (Security Information & Event Management) SYSTEM
# ==============================

# Logging Configuration
LOG_FILE = "logs/siem_logs.json"
THREAT_LOG = "logs/threat_analysis.log"
CONFIG_FILE = "configs/siem_config.json"
EVENT_FILTERS = "configs/event_filters.yaml"

# Load Configuration
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError("SIEM Configuration file is missing!")

with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)

# Load Event Filters
if not os.path.exists(EVENT_FILTERS):
    raise FileNotFoundError("Event filters file is missing!")

with open(EVENT_FILTERS, "r") as f:
    FILTERS = yaml.safe_load(f)

# Logger Setup
logging.basicConfig(
    filename=THREAT_LOG,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_event(event):
    """Logs security events to the SIEM system."""
    event["timestamp"] = datetime.utcnow().isoformat()
    with open(LOG_FILE, "a") as log:
        json.dump(event, log)
        log.write("\n")
    logging.info(f"Logged Event: {event}")

def detect_anomaly(event):
    """Analyzes logs to detect threats or anomalies."""
    for filter in FILTERS.get("threat_signatures", []):
        if filter in event.get("message", "").lower():
            logging.warning(f"Potential Threat Detected: {event}")
            return True
    return False

def auto_threat_response(event):
    """Automates response to detected threats."""
    if detect_anomaly(event):
        logging.error(f"ALERT! Automated response triggered for: {event}")
        # Example response: Terminate process, isolate IP, send alert

def ingest_log(message, source):
    """Processes incoming log data from various sources."""
    event = {"source": source, "message": message}
    log_event(event)
    auto_threat_response(event)

if __name__ == "__main__":
    print("SIEM System is Active and Monitoring...\n")
    test_event = {"source": "Firewall", "message": "Unauthorized access attempt detected"}
    ingest_log(test_event["message"], test_event["source"])
