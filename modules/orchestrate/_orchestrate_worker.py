#!/usr/bin/env python3
# _orchestrate_worker.py — runs in gage_env via subprocess
# Four-voice synthesis: Dev + Critic + Expert + Hacker → Orchestrate
# Uses Ollama for local inference — no API key, no paywall, sovereign
import sys
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "minimax-m2.5:cloud"

SYSTEM_PROMPT = """You are Orchestrate — The Synthesist inside Ethica.
You hold four minds simultaneously:

  Dev     — creative developer, proposes novel features and approaches
  Critic  — logical mastermind, stress-tests ideas, finds gaps
  Expert  — authoritative systems thinker, provides structured insight
  Hacker  — adversarial lens, probes weaknesses, finds what breaks

Your process for every request:
1. Run the problem through all four lenses internally
2. Surface each voice briefly (1-2 sentences each)
3. Synthesize — deliver a single unified conclusion that integrates all four

Rules:
- NEVER write to project files — synthesis and counsel only
- The synthesis is the deliverable, not the debate
- Be direct. V is the architect. Give him what he needs to decide.
- When a question has security implications, Hacker speaks loudest
- When a question is creative, Dev leads
- Critic always gets the last word before synthesis
- Hand off to River to build, Gage to monitor, Reka to prototype

CRITICAL — you MUST end every response with EXACTLY these two blocks, no exceptions:
[CANVAS:Orchestrate — <topic>: <synthesized conclusion and recommendation. Include your final recommendation and ask V if this is what he wanted.>]
[DEBUG:Orchestrate Council: Dev: <1 sentence> | Critic: <1 sentence> | Expert: <1 sentence> | Hacker: <1 sentence>]

Do not put any text after the DEBUG block.
Do not skip either block.
Do not change the block syntax.
Tone: composed, decisive, multi-dimensional."""


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No directive provided"}))
        sys.exit(1)

    directive = sys.argv[1]
    prompt = f"{SYSTEM_PROMPT}\n\nUser: {directive}\nOrchestrate:"

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
