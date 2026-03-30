import os
import json
from datetime import datetime
from pathlib import Path

REFLECTIONS_DIR = Path("/home/nine9/SoulGate/Guardian/WhiteRabbitNeo/reflections")

class ReflectionMirror:
    def __init__(self):
        self.reflections = self.load_all_reflections()

    def load_all_reflections(self):
        data = []
        for file in REFLECTIONS_DIR.glob("reflection_*.json"):
            try:
                with open(file, 'r') as f:
                    content = json.load(f)
                    data.append(content)
            except Exception as e:
                print(f"[ERROR] Reading {file}: {e}")
        return data

    def summarize_behavior(self):
        summary = {}
        for entry in self.reflections:
            profile = entry.get("matched_profile")
            label = profile["label"] if isinstance(profile, dict) else "unclassified"
            summary[label] = summary.get(label, 0) + 1
        return summary

    def show_timeline(self):
        timeline = sorted(self.reflections, key=lambda x: x["timestamp"])
        for entry in timeline:
            ts = entry["timestamp"]
            label = entry.get("matched_profile", {}).get("label", "unclassified")
        print(f"[{ts}] → {label}")

# Test pulse
if __name__ == "__main__":
    mirror = ReflectionMirror()
    print("\n🪞 Behavior Summary:")
    for k, v in mirror.summarize_behavior().items():
        print(f"- {k}: {v} events")

    print("\n🧭 Timeline:")
    mirror.show_timeline()
