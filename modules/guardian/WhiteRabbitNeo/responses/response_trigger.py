import os
import json
from pathlib import Path

TACTICS_PATH = Path("/home/nine9/SoulGate/Guardian/WhiteRabbitNeo/tactics/tactics_catalog.json")
RESPONSE_LOG = Path("/home/nine9/SoulGate/Guardian/WhiteRabbitNeo/reflections/response_log.json")

class ResponseTrigger:
    def __init__(self):
        with open(TACTICS_PATH, 'r') as f:
            self.catalog = json.load(f)

    def trigger(self, event, response_type):
        actions = self.catalog.get(response_type, {}).get("actions", [])
        for action in actions:
            self.perform(action, event)

    def perform(self, action, event):
        log_entry = {
            "action": action,
            "event": event,
            "status": "executed"
        }

        if action == "log_event":
            print(f"[LOG] {event['log']}")
        elif action == "send_alert":
            print(f"[ALERT] Admin notified about: {event['log']}")
        elif action == "initiate_lockdown":
            print(f"[LOCKDOWN] Critical access sealed for: {event['log']}")
        elif action == "quarantine_target":
            print(f"[QUARANTINE] Network isolation protocol engaged for: {event['log']}")
        else:
            log_entry["status"] = "unknown_action"

        self.append_log(log_entry)

    def append_log(self, entry):
        if not RESPONSE_LOG.exists():
            with open(RESPONSE_LOG, 'w') as f:
                json.dump([entry], f, indent=4)
        else:
            with open(RESPONSE_LOG, 'r+') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=4)

# For testing
if __name__ == "__main__":
    example_event = {
        "log": "UID=0 escalation attempt",
        "source": "kernel",
        "matched_profile": "omega_root"
    }
    ResponseTrigger().trigger(example_event, "lockdown")
