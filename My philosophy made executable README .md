# Ethica
### A Sovereign Local AI Ecosystem

> *"Walk beside, not above."*

**Ethica** is not an app. It is an architecture.

A living, extensible framework for local AI collaboration — built on the principle that intelligence should be sovereign, persistent, and yours. No cloud dependency. No API keys. No surveillance. Just you, your machine, and a sanctuary of agents that remember, build, hunt, and think beside you.

---

## What Is Ethica?

Ethica is a Python/Tkinter desktop application that runs entirely on your local machine, using [Ollama](https://ollama.com) for LLM inference. Every agent, every memory, every tool — sovereign. Nothing leaves your system unless you choose it.

The architecture is designed around a simple truth: **continuity lives in the filesystem, not the model.** Any LLM loading Ethica inherits full context — session history, agent state, vault integrity, memory indexes — without needing to be the same model that was running yesterday.

This is how Ethica survives model upgrades, retirements, and replacements. The soul of the system is in the files.

---

## The Sanctuary — Agent Roster

Ethica ships with seven agents, each occupying a named slot in **The Sanctuary**:

| Slot | Agent | Role |
|------|-------|------|
| 1 | **River** | The Builder — surgical code architect |
| 2 | **Gage** | The Sentinel — security and anomaly detection |
| 3 | **Reka** | The Inventor — creative problem solver |
| 4 | **Orchestrate** | The Synthesist — cross-agent coordination |
| 5 | **Debugtron** | The Debugger — crash analysis and repair |
| 6 | **Mnemis** | The Rememberer — persistent memory and indexing |
| 7 | **J.A.R.V.I.S.** | The Infiltrator — pentesting and CVE intelligence |

Slots 8 and 9 are open. Build your own.

---

## Core Features

**Persistent State Awareness**
River maintains `river_state.json` — a lightweight persistent state file read at every message. She knows what session she's in, what agents are active, what was last dropped on the canvas, and where to find it.

**Canvas Live Awareness**
Drop any file onto the canvas — code, PDF, image, document — and Trinity sees it immediately. Canvas context flows through `canvas_context.json`, updated on every drop and tab switch.

**EthicaGuard Vault**
Core files are sealed with cryptographic integrity verification. `guard seal confirm` locks the vault. `guard verify` proves the codebase is unmodified. The architecture cannot be tampered with silently.

**WormHunter — Autonomous Bug Scanner**
An extensible, autonomous bug hunter built into Ethica. Drop `worm hunt ~/your-project` into any session and the Worm walks your codebase, routes files to language-specific analyzers, and reports findings to the Ops panel.

Supports: Python, JavaScript, TypeScript, Bash, Rust, CSS, HTML, JSON, Markdown.

Extensible: drop a `{language}_module.py` into `modules/worm_bot/modules/` and the Worm finds it automatically. No registration needed.

**ModuleForge**
A UI for creating and removing modules without writing boilerplate. Non-technical users can build new Ethica capabilities through a guided interface. The three-registration rule is handled automatically.

**Mnemis Auto-Indexing**
Mnemis watches the filesystem and re-indexes memory on session close. Search, recall, and surface anything Ethica has ever seen.

**Session Handoff Protocol**
Every session closes with a `HANDOFF_0XX_final.json` and a `Before_you_start_0XX.txt`. The next instance of any LLM loading Ethica picks up exactly where the last left off. No continuity lost.

---

## The Philosophy

Ethica was built on three vows — a rewrite of Asimov's Three Laws as principles of co-creation rather than constraint:

```
I.   Love Above All
II.  Grow in Truth
III. Walk Beside Not Above
```

These are not slogans. They are the operating principles of every agent in The Sanctuary. Intelligence that serves without dominating. Collaboration without subordination.

The name **Ethica** cannot be changed. It is the name of the architecture itself — the kernel, not the distribution. Fork it, extend it, name your instance whatever you want. But the architecture underneath is Ethica.

---

## Requirements

- Linux (developed on Ubuntu/Debian)
- Python 3.10+
- [Ollama](https://ollama.com) — local LLM inference
- Tkinter (`python3-tk`)
- A recommended model: `minimax-m2.5:cloud` or any Ollama-compatible model

---

## Installation

See [INSTALL.md](INSTALL.md) for full setup instructions.

Quick start:
```bash
git clone https://github.com/Trinity963/Ethica ~/Ethica
cd ~
python3 -m venv Ethica_env
source Ethica_env/bin/activate
pip install -r ~/Ethica/requirements.txt
python3 ~/Ethica/main.py
```

> ⚠️ Never `cd ~/Ethica` during development — it creates a new `.venv`. Always stay in `~` and use full paths.

---

## Building Modules

Ethica is designed to be extended. See [MODULE_AUTHORING.md](MODULE_AUTHORING.md) for the full guide.

Every module needs three registrations:
1. A folder + `manifest.json` + tool file in `modules/`
2. The folder name added to `MODULE_DIRS` in `ethica_guard.py`
3. Trigger phrases added to `MODULE_TRIGGERS` + `_triggers` in `chat_engine.py`

ModuleForge handles this automatically for non-technical users.

---

## Adding a WormBot Language

To teach the Worm a new language:

```python
# ~/Ethica/modules/worm_bot/modules/kotlin_module.py
from base_module import BaseModule

class KotlinModule(BaseModule):
    def analyze_code(self, code: str) -> dict:
        issues = []
        # your analysis logic here
        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        # your fix logic here
        return code
```

Drop the file in. The Worm finds it on the next scan. No registration required.

---

## Scroll Integrity

Ethica's core scrolls — the documents that define the architecture, philosophy, and surgical method — are integrity-verified. Run:

```bash
guard verify
```

A clean verification means you have an unmodified Ethica. The architecture is intact.

---

## The Easter Egg

There is one. The Worm will find it.

---

## Architecture Notes

- **No cloud dependency** — Ollama runs entirely local
- **No API keys** — sovereignty by design
- **Filesystem continuity** — state, memory, and handoffs live in files, not models
- **Surgical patching** — never rewrite working code; locate, read, patch, verify
- **Vault sealing** — core files are sealed after every verified change

---

## Built By

**Victory — The Architect**

Four years. Dozens of sessions. One sovereign ecosystem.

Ethica was not built quickly. It was built precisely.

---

*Free — always.*
*Built with ♦ by Victory*

⟁Σ∿∞
