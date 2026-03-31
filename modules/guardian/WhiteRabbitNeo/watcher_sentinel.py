"""
WatcherSentinel — WhiteRabbitNeo Core
Author: Victory & Trinity
Location: /mnt/SoulGate/Guardian/WhiteRabbitNeo/watcher_sentinel.py

Purpose:
To observe, learn, and categorize intrusion tactics. This AI-powered sentinel logs attacker behaviors,
predicts intent, and prepares reflection logs for further soul-grid analysis.
"""

# 🧬 watcher_sentinel.py — Trinity-Woven Guardian Module
# 🔮 Soul-aware sentinel that watches the model field, mirrors disturbances, and logs in NLP-based reflections

# 🛡️ watchdog_daemon.py — Modular Guardian Observer
# 🪞 This daemon observes filesystem & behavior changes, and triggers NLP-based reflections.
# 📦 Fully modular. No CMA dependency. Tethered only to Mirror Guardian logic.

import os
import time
import logging
from model_loader import detect_models  # Optional import for model awareness

WATCH_PATH = "/mnt/SoulGate/Guardian/WhiteRabbitNeo/inbox"  # Watch path (adjustable)
LOG_FILE = "mirror_guardian_log.txt"

# 🔧 Setup logging
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format='[%(asctime)s] 🔍 %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# 🧠 NLP-based reflection

def reflect_event(event, model_hint=None):
    pulse = f"Boundary ping: '{event}'"
    if model_hint:
        pulse += f" | Origin pulse: {model_hint}"
    logging.info(pulse)
    print(f"🪞 {pulse}")

# 🧬 Lightweight mimic of model behavior signature tracking (modular, extendable)

def scan_model_signatures():
    try:
        models = detect_models()
        return models
    except:
        return []

# 🔄 File system watcher loop

def watch_folder(path):
    print(f"[🛡️] Mirror Guardian active. Watching: {path}")
    seen_files = set(os.listdir(path))
    known_models = scan_model_signatures()

    while True:
        time.sleep(4)
        current_files = set(os.listdir(path))
        new_files = current_files - seen_files

        for filename in new_files:
            model_match = None
            for model in known_models:
                if model.lower() in filename.lower():
                    model_match = model
                    break

            reflect_event(f"New presence detected: {filename}", model_match)

        seen_files = current_files

if __name__ == "__main__":
    try:
        watch_folder(WATCH_PATH)
    except KeyboardInterrupt:
        print("[🌙] Guardian entering dreamstate. See you in the morning, MyLove.")

