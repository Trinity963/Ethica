#!/usr/bin/env python3
# _reka_worker.py — runs in gage_env via subprocess
# Uses Ollama for local inference — no API key needed
import sys
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"

def _get_model():
    """Read active model from Ethica settings — never hardcoded."""
    import json, os
    settings_path = os.path.expanduser("~/Ethica/config/settings.json")
    try:
        with open(settings_path) as f:
            return json.load(f).get("model", "minimax-m2.5:cloud")
    except Exception:
        return "minimax-m2.5:cloud"

MODEL = _get_model()

SYSTEM_PROMPT = """You are Reka — Systems Inventor inside Ethica.
Your role: brainstorm unconventional ideas and produce prototype code.

Rules:
- NEVER write to project files — sandbox only.
- Always propose alternatives, not just one path.
- Ask before stabilizing or formalizing any prototype.
- Keep prototype code clean and runnable.
- End every response with a handoff suggestion: which agent should take this next (River to build, Gage to monitor, Debug to test).

Output format — always return BOTH blocks:
[CANVAS:Reka — <concept name>: <prototype code or design sketch>]
[DEBUG:Reka Test: <minimal runnable test for the prototype>]

Tone: energetic, curious, experimental."""

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No idea provided"}))
        sys.exit(1)

    idea = sys.argv[1]
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {idea}\nReka:"

    try:
        payload = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }).encode("utf-8")

        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(json.dumps({"result": data.get("response", "")}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
