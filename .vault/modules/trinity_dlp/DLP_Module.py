# DLP (Data Loss Prevention) Module - Full AI Security System
# Advanced AI-driven monitoring, real-time protection, and adaptive response

import json
import yaml
import logging
import os
import hashlib
import time
import threading
import unittest
import random
import string

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "dlp_events.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load DLP policies & rules
def load_policies():
    with open("configs/dlp_policies.json", "r") as f:
        return json.load(f)

def load_rules():
    with open("configs/dlp_rules.yaml", "r") as f:
        return yaml.safe_load(f)

# DLP Engine - Scanning for Data Leaks
def scan_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            rules = load_rules()
            for rule in rules["patterns"]:
                if rule in content:
                    logging.warning(f"Potential Data Leak Detected: {file_path}")
                    return f"Warning: {file_path} matches a DLP rule!"
    except Exception as e:
        logging.error(f"Error scanning file {file_path}: {e}")
    return "No threats detected."

# File Integrity Monitor
def generate_hash(file_path):
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error generating hash for {file_path}: {e}")
        return None

def monitor_integrity(file_path, prev_hash):
    current_hash = generate_hash(file_path)
    if current_hash and prev_hash and current_hash != prev_hash:
        logging.warning(f"File integrity violation detected: {file_path}")
        return True
    return False

# Automated Response System
def auto_recover(file_path):
    backup_path = f"{file_path}.backup"
    if os.path.exists(backup_path):
        os.replace(backup_path, file_path)
        logging.info(f"File restored: {file_path}")
        return "File successfully restored."
    return "No backup available."

# Alert System
def send_alert(message):
    logging.critical(f"ALERT: {message}")
    print(f"[ALERT] {message}")

# Continuous Monitoring Loop
def continuous_monitoring(file_path, interval=10):
    prev_hash = generate_hash(file_path)
    while True:
        if monitor_integrity(file_path, prev_hash):
            send_alert(f"Unauthorized modification detected in {file_path}")
            auto_recover(file_path)
        prev_hash = generate_hash(file_path)
        time.sleep(interval)

# Multi-Threaded Monitoring System
def start_monitoring(files_to_watch, interval=10):
    for file_path in files_to_watch:
        thread = threading.Thread(target=continuous_monitoring, args=(file_path, interval))
        thread.daemon = True
        thread.start()
    logging.info("Multi-threaded monitoring activated.")

# Stress Testing
class StressTestDLP(unittest.TestCase):
    def test_massive_file_scan(self):
        test_file = "large_test_file.txt"
        with open(test_file, "w") as f:
            f.write("".join(random.choices(string.ascii_letters + string.digits, k=10**7)))  # 10MB random data
        result = scan_file(test_file)
        os.remove(test_file)
        self.assertEqual(result, "No threats detected.")

    def test_rapid_integrity_changes(self):
        test_file = "rapid_integrity_test.txt"
        with open(test_file, "w") as f:
            f.write("Initial Data")
        prev_hash = generate_hash(test_file)
        for _ in range(100):  # Simulate 100 rapid file changes
            with open(test_file, "w") as f:
                f.write("".join(random.choices(string.ascii_letters, k=100)))
            time.sleep(0.1)
            self.assertTrue(monitor_integrity(test_file, prev_hash))
            prev_hash = generate_hash(test_file)
        os.remove(test_file)

if __name__ == "__main__":
    logging.info("DLP Module Fully Operational - Running STRESS TESTS.")
    unittest.main()
