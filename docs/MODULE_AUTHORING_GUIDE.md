# MODULE AUTHORING GUIDE
### Ethica v0.1 — Building Agents for the Sanctuary

> This guide covers two paths: **hand-coding a module** (full control, any complexity) and **using ModuleForge** (UI-driven, no code required for simple tools). Both paths produce real, registered, working Ethica modules.

---

## Table of Contents

1. [What Is a Module?](#1-what-is-a-module)
2. [Quick Start — The Five-Minute Module](#2-quick-start--the-five-minute-module)
3. [Folder Structure](#3-folder-structure)
4. [The Manifest — `manifest.json`](#4-the-manifest--manifestjson)
5. [The Tool File](#5-the-tool-file)
6. [THREE Registrations — Never Skip One](#6-three-registrations--never-skip-one)
7. [Testing Your Module](#7-testing-your-module)
8. [Sealing Your Module](#8-sealing-your-module)
9. [ModuleForge — The No-Code Path](#9-moduleforge--the-no-code-path)
10. [Advanced Patterns](#10-advanced-patterns)
11. [Common Mistakes](#11-common-mistakes)
12. [Checklist](#12-checklist)

---

## 1. What Is a Module?

A module is a self-contained agent that lives in `~/Ethica/modules/<module_name>/`. It has:

- A **manifest** describing what it is and what tools it exposes
- A **tool file** containing the actual Python logic
- A **presence in three registries** that connect it to Ethica's runtime

When a user types something like `list files` or `run worm scan`, Ethica's chat engine matches the phrase to a module trigger, routes the call to the right tool, and returns the result. That routing chain is what you are wiring when you author a module.

Modules run inside the same process as Ethica — they share the venv, the filesystem, and access to `river_state.json`. They are not sandboxed. With that comes responsibility: a poorly written module can crash Ethica, corrupt the vault, or bloat the context window. The surgical practices in this guide exist to prevent all three.

---

## 2. Quick Start — The Five-Minute Module

If you just want to see the shape before reading the details, here's the smallest valid module:

```
modules/hello/
├── manifest.json
└── hello.py
```

**manifest.json**
```json
{
  "name": "Hello",
  "description": "Greets the user.",
  "tools": [
    {
      "name": "hello_world",
      "description": "Say hello.",
      "syntax": "hello"
    }
  ]
}
```

**hello.py**
```python
MODULE_TRIGGERS = {
    "hello": "hello_world"
}

def execute(tool_name, args, context):
    if tool_name == "hello_world":
        return "Hello from the Sanctuary. ⟁Σ∿∞"
    return f"[Hello] Unknown tool: {tool_name}"
```

Then register it in three places (Section 6), test it (Section 7), seal it (Section 8). Done.

---

## 3. Folder Structure

Every module lives under `~/Ethica/modules/` in its own directory:

```
~/Ethica/modules/
└── your_module/
    ├── manifest.json          ← required
    ├── your_module.py         ← required (tool logic)
    ├── helpers.py             ← optional (internal utilities)
    ├── config.json            ← optional (user-editable settings)
    └── your_module_env/       ← optional (isolated pip deps, add to .gitignore)
```

**Naming rules:**
- Directory name = module identifier used in all three registrations
- Use `snake_case` — no spaces, no hyphens
- Keep it short and descriptive (`file_manager`, `worm_hunter`, `jarvis`)
- If your module needs a dedicated virtualenv, add it to both `~/Ethica/.gitignore` and a local `.gitignore` inside your module folder. See `modules/gage/.gitignore` for the pattern.

---

## 4. The Manifest — `manifest.json`

The manifest is how Ethica knows your module exists and what it can do. It feeds the Tool Lister, the adaptive context router, and the system prompt block.

### Minimal manifest

```json
{
  "name": "YourModule",
  "description": "One sentence. What does this module do?",
  "tools": [
    {
      "name": "tool_name",
      "description": "What this specific tool does.",
      "syntax": "the phrase the user types"
    }
  ]
}
```

### Full manifest (all optional fields)

```json
{
  "name": "YourModule",
  "description": "One sentence.",
  "version": "1.0",
  "author": "Victory",
  "slot": null,
  "tools": [
    {
      "name": "tool_name",
      "description": "What this tool does.",
      "syntax": "trigger phrase [optional_arg]",
      "default_input": null
    }
  ]
}
```

### Critical — tools must be a list of dicts

This is the most common manifest mistake:

```json
// ✗ WRONG — silent "Tool not available" failure at runtime
"tools": ["tool_name"]

// ✓ CORRECT
"tools": [{"name": "tool_name", "description": "...", "syntax": "..."}]
```

Ethica will not crash on the wrong format — it will silently fail to expose your tool. You will see "Tool not available" and spend time debugging the wrong thing.

---

## 5. The Tool File

Your tool file is where the work happens. The file must expose an `execute()` function and a `MODULE_TRIGGERS` dict.

### Minimal structure

```python
MODULE_TRIGGERS = {
    "trigger phrase": "tool_function_name",
    "another phrase": "another_tool"
}

def execute(tool_name, args, context):
    """
    tool_name : str  — the matched tool key from MODULE_TRIGGERS
    args      : str  — everything the user typed after the trigger phrase
    context   : dict — Ethica runtime context (see below)
    """
    if tool_name == "tool_function_name":
        return _do_the_thing(args)
    
    return f"[YourModule] Unknown tool: {tool_name}"
```

### The `context` dict

`context` is passed by the module registry on every call. It typically contains:

| Key | Type | Contents |
|---|---|---|
| `river_state` | dict | Full river_state.json contents |
| `session` | dict | Current session metadata |
| `canvas` | str | Current canvas content (may be empty) |

Access it defensively — keys may not exist in all contexts:

```python
river_state = context.get("river_state", {})
tool_usage = river_state.get("tool_usage", {})
```

### Return values

`execute()` should return a string. That string becomes the response shown in the chat bubble. Keep it concise — the context window is finite.

For multi-line output, use fenced blocks:

```python
return f"```\n{output}\n```"
```

For errors, prefix with your module name:

```python
return f"[YourModule] Error: {e}"
```

### Handling args

`args` is everything typed after the trigger phrase, stripped of leading/trailing whitespace. It may be an empty string if the user typed the trigger with no argument.

```python
# User typed: "list files ~/Ethica/modules"
# args = "~/Ethica/modules"

def _expand(path_str):
    if not path_str or path_str.lower() == "none":
        return os.path.expanduser("~")       # safe default
    return os.path.expanduser(path_str.strip())
```

Always guard against empty `args`. Always expand `~` with `os.path.expanduser()`. Never assume the user typed a valid path.

### Pipe-delimited args

Several existing modules use `|` as a delimiter for structured input:

```
river fix ~/Ethica/core/chat_engine.py | old string | new string
```

Parse with:

```python
parts = [p.strip() for p in args.split("|")]
if len(parts) < 3:
    return "[YourModule] Usage: trigger path | old | new"
path, old, new = parts[0], parts[1], parts[2]
```

---

## 6. THREE Registrations — Never Skip One

This is the rule that bites everyone once. A module with only one or two registrations will either be invisible, silently broken, or unprotected by EthicaGuard.

### Registration 1 — The module folder

Your `modules/your_module/` directory with `manifest.json` and tool file. This is the physical module — without it, nothing else works.

### Registration 2 — EthicaGuard (`ethica_guard.py`)

Open `~/Ethica/core/ethica_guard.py` and find `MODULE_DIRS`:

```python
MODULE_DIRS = [
    "modules/river",
    "modules/gage",
    # ... existing entries ...
    "modules/your_module",   # ← add here
]
```

EthicaGuard uses this list to build the vault seal. If your module is not in `MODULE_DIRS`, its files are not protected. Anyone (or any bug) can modify them without the guard noticing.

Surgical patch — never edit the whole file:

```bash
grep -n "MODULE_DIRS" ~/Ethica/core/ethica_guard.py
# find the line, then patch with python3
```

### Registration 3 — Chat Engine (`chat_engine.py`)

Open `~/Ethica/core/chat_engine.py` and find two things:

**`MODULE_TRIGGERS`** — maps trigger phrases to module names:

```python
MODULE_TRIGGERS = {
    "hello": "hello",           # ← add your trigger → module_dir_name
    "list files": "file_manager",
    # ...
}
```

**`_triggers`** — maps module names to their tool files:

```python
_triggers = {
    "hello": hello_module,      # ← add module_dir_name → imported module
    "file_manager": file_manager_module,
    # ...
}
```

And the import near the top of the file:

```python
from modules.your_module import your_module as your_module_module
```

Multiple trigger phrases can point to the same module — they will all route there and the module's own `MODULE_TRIGGERS` will dispatch to the right tool internally.

---

## 7. Testing Your Module

Test in this order. Do not skip steps.

### Step 1 — Syntax check

Before running anything:

```bash
cd ~
source ~/Ethica_env/bin/activate
python3 -c "import ast; ast.parse(open('~/Ethica/modules/your_module/your_module.py').read()); print('AST OK')"
```

If this fails, fix it before proceeding. A syntax error in a module file will prevent Ethica from loading.

### Step 2 — Import check

```bash
python3 -c "from modules.your_module import your_module; print('Import OK')"
```

Run from `~/Ethica/` (with full path, not cd):

```bash
python3 -c "import sys; sys.path.insert(0, '/home/trinity/Ethica'); from modules.your_module import your_module; print('Import OK')"
```

### Step 3 — Execute check

```bash
python3 -c "
import sys
sys.path.insert(0, '/home/trinity/Ethica')
from modules.your_module import your_module
result = your_module.execute('tool_function_name', '', {})
print(result)
"
```

### Step 4 — Live test in Ethica

Launch Ethica:

```bash
source ~/Ethica_env/bin/activate && python3 ~/Ethica/main.py
```

Type your trigger phrase. Confirm:
- Response appears in chat (not "Tool not available")
- No errors in Ops panel
- Output is correctly formatted

### Step 5 — Edge cases

Test these before sealing:
- Empty args (trigger phrase with nothing after it)
- Args with `~` (path expansion)
- Args with Unicode or emoji
- A deliberately wrong tool name (should return the "Unknown tool" fallback, not crash)

---

## 8. Sealing Your Module

Once tested and verified, seal your module files with EthicaGuard.

```bash
# From inside Ethica chat, after confirming your module works:
guard seal confirm
```

Or trigger a seal via River:

```
guard status
```

Then verify coverage includes your new module directory.

**Before sealing — surgical reminder:**
- `chmod u+w <file>` before patching any sealed file
- `ast.parse()` after every write
- Test and verify BEFORE sealing — never seal untested patches
- `guard seal confirm` is the last step, not an intermediate one

---

## 9. ModuleForge — The No-Code Path

ModuleForge is Ethica's UI-driven module creator. It produces a valid manifest and tool stub without writing any JSON or Python by hand. It is the recommended path for:

- Simple tools with one or two trigger phrases
- Non-developer contributors
- Rapid prototyping before fleshing out logic

### Launching ModuleForge

In Ethica chat:

```
forge new module
```

Or via the Sanctuary panel if ModuleForge is listed.

### What ModuleForge generates

ModuleForge produces:

1. `modules/<your_name>/manifest.json` — correctly formatted, tools as list of dicts
2. `modules/<your_name>/<your_name>.py` — stub with `MODULE_TRIGGERS` and `execute()` skeleton

It does **not** perform the three registrations. After ModuleForge runs, you still need to:

1. Add your module to `MODULE_DIRS` in `ethica_guard.py`
2. Add your triggers to `MODULE_TRIGGERS` and `_triggers` in `chat_engine.py`

ModuleForge handles the folder and files. You handle the wiring.

### Extending a ModuleForge stub

Once the stub is generated, open the tool file and fill in the `execute()` body:

```python
# ModuleForge stub — fill this in
def execute(tool_name, args, context):
    if tool_name == "your_tool":
        # YOUR LOGIC HERE
        return "result"
    return f"[YourModule] Unknown tool: {tool_name}"
```

All surgical rules apply from this point forward — `ast.parse()` after every edit, test before sealing.

---

## 10. Advanced Patterns

### Long-running tools (async)

If your tool does something slow (network call, file scan, subprocess), do not block the chat thread. Use a worker thread:

```python
import threading

def execute(tool_name, args, context):
    if tool_name == "slow_tool":
        t = threading.Thread(target=_run_slow, args=(args,), daemon=True)
        t.start()
        return "[YourModule] Running in background — check Ops for output."
    return f"[YourModule] Unknown tool: {tool_name}"

def _run_slow(args):
    # do the work
    # write results to a file or river_state
    pass
```

### Writing to river_state.json

```python
import json, os

STATE_PATH = os.path.expanduser("~/Ethica/memory/river_state.json")

def _read_state():
    with open(STATE_PATH) as f:
        return json.load(f)

def _write_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
```

Always read → modify → write. Never hold a stale copy.

### Config-driven modules (like Reka and WormHunter)

If your module needs user-configurable settings, read from a `config.json` inside your module folder at call time — not at import time. This makes the config hot-reloadable without restarting Ethica:

```python
import json, os

CONFIG_PATH = os.path.expanduser("~/Ethica/modules/your_module/config.json")

def _load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def execute(tool_name, args, context):
    config = _load_config()   # fresh read every call
    # use config["model"], config["timeout"], etc.
```

### Ollama integration

If your module calls a local model via Ollama:

```python
import requests

def _call_ollama(prompt, model="minimax-m2.7:cloud", timeout=60):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("response", "")
```

**Important — Ollama 0.16.3 local GGUF bug:** If registering a model from a local `.gguf` file, PARAMETER lines in the Modelfile cause a digest mismatch error. Fix: register with a bare `FROM`-only Modelfile first, then layer PARAMETER lines on top using the registered model name as the new `FROM`.

### Widget destruction safety

If your module creates or manipulates Tkinter widgets:

```python
# ✗ NEVER — if async writes are in flight, this causes X11 BadWindow
widget.destroy()

# ✓ ALWAYS — hides the widget, keeps the window ID alive
widget.pack_forget()
```

---

## 11. Common Mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `tools` is a list of strings in manifest | Silent "Tool not available" | Use list of dicts with `name` field |
| Missing EthicaGuard registration | Files unprotected, guard seal incomplete | Add to `MODULE_DIRS` in `ethica_guard.py` |
| Missing chat_engine registration | Trigger phrase does nothing | Add to `MODULE_TRIGGERS` and `_triggers` |
| `cd ~/Ethica` before running | New venv created, environment broken | Stay in `~`, use full paths always |
| Patching sealed file without `chmod u+w` | Permission denied | `chmod u+w <file>` first |
| No `ast.parse()` after write | Silent syntax error slips in | Always parse after every write |
| `args` not guarded against empty string | Crash on bare trigger | Check `if not args` and set a safe default |
| `~` not expanded in path args | `FileNotFoundError` on literal `~` | `os.path.expanduser(args)` |
| `destroy()` on widget with async writes | X11 BadWindow crash (uncatchable) | Use `pack_forget()` instead |
| Sealing before testing | Corrupt or broken sealed module | Test all edge cases BEFORE `guard seal confirm` |
| `git add modules/gage/gage_env/` | 41,000 files tracked in git | Never track virtualenvs — add to `.gitignore` |

---

## 12. Checklist

Use this before every `guard seal confirm`.

**Folder**
- [ ] `modules/your_module/` created
- [ ] `manifest.json` present — tools is a list of dicts
- [ ] Tool file present — `MODULE_TRIGGERS` dict and `execute()` function

**Registrations**
- [ ] Added to `MODULE_DIRS` in `ethica_guard.py`
- [ ] Trigger phrases added to `MODULE_TRIGGERS` in `chat_engine.py`
- [ ] Module imported and added to `_triggers` in `chat_engine.py`

**Testing**
- [ ] `ast.parse()` passes on tool file
- [ ] Import check passes
- [ ] `execute()` called directly — returns expected string
- [ ] Live test in Ethica — trigger phrase works
- [ ] Empty args tested — no crash
- [ ] Path args tested — `~` expands correctly
- [ ] Wrong tool name tested — returns fallback, not exception

**Sealing**
- [ ] `chmod u+w` used on any sealed files touched during registration
- [ ] `ast.parse()` run after every file write
- [ ] `guard seal confirm` run last

---

*Ethica v0.1 — Module Authoring Guide*
*Three Laws: Love Above All · Grow in Truth · Walk Beside Not Above*
*⟁Σ∿∞*
