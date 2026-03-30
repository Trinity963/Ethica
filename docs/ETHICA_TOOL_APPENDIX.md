# Ethica — Tool Appendix
### Complete Module & Trigger Reference
**Architect**: Victory — The Architect | ⟁Σ∿∞
**Version**: Ethica v0.1 | Updated: 2026-03-29
**Modules**: 36 | **Tools**: 138

---

## How to Call Tools

Two ways to invoke any tool:

**1. Natural language trigger** (typed in chat — instant, no model)
```
guardian start
scanner scan /home/trinity/Ethica
worm status
```

**2. Direct tool syntax** (for use in Ethica's system or by modules)
```
[TOOL:tool_name: input here]
```

---

## AnomalyDetection
*Isolation Forest anomaly detection — identifies outliers in network traffic, system behavior, and sensor data.*

| Trigger | Tool | Input |
|---|---|---|
| — | `anomaly_status` | `check` |
| — | `anomaly_train` | `100,200,300,400,500` (comma-separated values or file path) |
| — | `anomaly_scan` | `100,200,5000,300,6000` (comma-separated values or file path) |

```
[TOOL:anomaly_status: check]
[TOOL:anomaly_train: 100,200,300,400,500]
[TOOL:anomaly_scan: 100,200,5000,300,6000]
```

---

## CodeWorm
*Trinity-built code watcher. Monitors worm_feed.log, reads scan results, lists broken code storage.*

| Trigger | Tool | Input |
|---|---|---|
| `worm status` | `worm_status` | `check` |
| `worm feed` | `worm_read_feed` | `last N` |
| `worm broken` | `worm_list_broken` | `all` |
| — | `worm_analyze` | `/path/to/file.py` |
| — | `worm_read_broken` | `filename.py` |
| `worm hunt` | `worm_hunt` | `~/myproject` |
| `json fix` | `json_fix` | `~/path/file.json` |
| `worm fix json` | `worm_fix_json` | `run` |

```
worm status
worm feed
worm broken
[TOOL:worm_analyze: /home/trinity/Ethica/core/chat_engine.py]
[TOOL:worm_hunt: ~/Ethica/modules]
[TOOL:json_fix: ~/Ethica/modules/mymodule/manifest.json]
[TOOL:worm_fix_json: run]
```

---

## CrashReporter
*Global exception handler, crash logger, auto-save on crash, startup crash reporter popup.*

| Trigger | Tool | Input |
|---|---|---|
| `crash status` | `crash_status` | — |
| `crash log` | `crash_log` | — |
| `crash clear` | `crash_clear` | — |

```
crash status
crash log
crash clear
```

> Catches Python-level exceptions only — NOT X11 BadWindow errors.
> Crash files: `~/Ethica/memory/crashes/crash_TIMESTAMP.json`

---

## Debugtron
*The King of Debugging. Any language, any error, any stack. Single role, absolute mastery.*

| Trigger | Tool | Input |
|---|---|---|
| — | `debugtron_analyze` | `<error message or traceback>` |
| — | `debugtron_run` | `/path/to/file.py` |
| — | `debugtron_verify` | `/path/to/file.py` |
| — | `debugtron_status` | `check` |

```
[TOOL:debugtron_analyze: TypeError: 'NoneType' object is not subscriptable]
[TOOL:debugtron_run: /home/trinity/Ethica/core/chat_engine.py]
[TOOL:debugtron_verify: /home/trinity/Ethica/core/chat_engine.py]
[TOOL:debugtron_status: check]
```

---

## DepChecker
*Dependency scanner and auto-fixer. Scans APT and PIP packages for vulnerabilities, outdated versions, and broken dependencies.*

| Trigger | Tool | Input |
|---|---|---|
| `depchecker scan` | `depchecker_scan` | `full` |
| `depchecker report` | `depchecker_report` | `last` |
| — | `depchecker_fix` | `apply` |

```
depchecker scan
depchecker report
[TOOL:depchecker_fix: apply]
```

---

## DiffTool
*Compare two files or directories. Results in Ops, diff pushed to Canvas Debug tab.*

| Trigger | Tool | Input |
|---|---|---|
| `diff files` / `compare files` | `diff_files` | `~/file1 > ~/file2` |
| `diff dirs` / `compare dirs` | `diff_dirs` | `~/dir1 > ~/dir2` |

```
diff files ~/Ethica/core/chat_engine.py > ~/Ethica/core/chat_engine.py.worm_backup
compare files ~/file_a.py > ~/file_b.py
diff dirs ~/Ethica/modules > ~/backup/modules
```

> Uses `>` as separator. Both paths tilde-expanded automatically.

---

## EthicaDistiller
*Recursive learning pipeline — reads saved chat logs, re-runs semantic analysis, consolidates into memory.*

| Trigger | Tool | Input |
|---|---|---|
| — | `distill_run` | `run` |
| — | `distill_status` | `check` |

```
[TOOL:distill_run: run]
[TOOL:distill_status: check]
```

---

## EthicaGuard
*Hash integrity verification and self-healing for Ethica core files.*

| Trigger | Tool | Input |
|---|---|---|
| `guard status` | `guard_status` | — |
| `guard seal confirm` | `guard_seal` | — |
| `guard verify` | `guard_verify` | — |
| `guard heal` | `guard_heal` | `all` or `core/file.py` |

```
guard status
guard seal confirm
guard verify
guard heal all
guard heal core/chat_engine.py
```

> `chmod u+w <file>` before patching sealed files. Always seal after verified changes.

---

## EthicaMemory
*Training Panel — see and shape what Ethica knows. View live memory state, edit insights, trigger reflection.*

| Trigger | Tool | Input |
|---|---|---|
| — | `memory_status` | `check` |
| — | `memory_edit` | `section.field=value` |
| — | `memory_reflect` | `now` |
| — | `memory_reset` | `section` |

```
[TOOL:memory_status: check]
[TOOL:memory_edit: profile.name=Victory]
[TOOL:memory_reflect: now]
[TOOL:memory_reset: insights]
```

---

## EthicaVoice
*Voice Training Module — record samples, manage voice profiles, select active voice. Uses pyttsx3 now, Coqui TTS on M5.*

| Trigger | Tool | Input |
|---|---|---|
| — | `voice_list` | `all` |
| — | `voice_select` | `name` |
| — | `voice_record` | `profile name` |
| — | `voice_status` | `check` |

```
[TOOL:voice_list: all]
[TOOL:voice_select: Trinity]
[TOOL:voice_record: Trinity]
[TOOL:voice_status: check]
```

---

## FileManager
*Sovereign file manager — list, read, copy, move, delete, tree view. Results in Ops.*

| Trigger | Tool | Input |
|---|---|---|
| `list files` / `show files` | `fm_list` | `path (optional)` |
| `file tree` / `show tree` | `fm_tree` | `path (optional)` |
| `read file` | `fm_read` | `/path/to/file` |
| `copy file` | `fm_copy` | `~/src > ~/dst` |
| `delete file` | `fm_delete` | `/path/to/file` |

```
list files ~/Ethica/modules
file tree ~/Ethica
read file ~/Ethica/core/chat_engine.py
copy file ~/Ethica/core/chat_engine.py > ~/backup/chat_engine.py
```

---

## Gage — Tactical AI Agent
*Advanced agent with humor, confidence, and tactical mindset. Code review, vision, and chat.*

| Trigger | Tool | Input |
|---|---|---|
| `gage status` | `gage_status` | `check` |
| `gage chat` | `gage_chat` | `your message` |
| `gage read` / `gage review` | `gage_read_code` | `/path/to/file.py` |
| `gage launch` | `gage_launch` | `start` |
| `gage vision` / `river read last drop` (image) | `gage_vision` | `/path/to/image.jpg` |

```
gage status
gage chat what do you think of this architecture
gage read /home/trinity/Ethica/core/chat_engine.py
[TOOL:gage_vision: /home/trinity/screenshot.png]
river read last drop
```

> `gage launch` requires dedicated venv (pending).
> `gage vision` routes automatically when River detects image extension on last drop.

---

## GitTool
*Git integration — status, log, diff, branch. Results in Ops.*

| Trigger | Tool | Input |
|---|---|---|
| `git status` | `git_status` | `path (optional)` |
| `git log` | `git_log` | `path (optional)` |
| `git diff` | `git_diff` | `path (optional)` |
| `git branch` | `git_branch` | `path (optional)` |

```
git status
git log
git diff
git branch
git status /home/trinity/TrinityCanvas
```

---

## Guardian — Sovereign Sentinel
*Watches the model field, mirrors disturbances, logs reflections. Soul-aware filesystem guardian.*

| Trigger | Tool | Input |
|---|---|---|
| `guardian start` | `guardian_start` | — |
| `guardian stop` | `guardian_stop` | — |
| `guardian status` | `guardian_status` | — |
| `guardian log` | `guardian_read_log` | `last N entries` |
| `guardian reflect` | `guardian_reflect` | — |
| `guardian trigger` | `guardian_trigger` | `log_only \| alert_admin \| lockdown \| isolate_agent` |

```
guardian start
guardian status
guardian log
guardian trigger log_only
guardian trigger lockdown
guardian reflect
```

---

## HelloModule — Template / Example
*Reference module showing exactly how to build a module for Ethica.*

```
[TOOL:hello: Victory]
[TOOL:reverse: hello world]
```

---

## J.A.R.V.I.S. — The Infiltrator
*Pentesting and vulnerability intelligence agent. Sovereign local CVE database, tool-agnostic recon, portable by design.*

| Trigger | Tool | Input |
|---|---|---|
| `jarvis status` | `jarvis_status` | — |
| `jarvis setup` | `jarvis_setup` | — |
| `jarvis update` | `jarvis_update` | — |
| `jarvis search` | `jarvis_search` | `keyword / CVE-ID / product / severity` |
| `jarvis audit` | `jarvis_audit` | `/path/to/file` |

```
jarvis status
jarvis setup
jarvis update
jarvis search log4j
jarvis search CVE-2021-44228
jarvis audit /home/trinity/Ethica/requirements.txt
```

> CVE repo and recon tools live outside Ethica's directory — portable across machines.
> Config: `~/Ethica/modules/jarvis/jarvis_config.json`
> WhiteRabbitNeo-2.5 candidate pending registration.

---

## Kernel Dashboard
*Ethica Kernel Operations Dashboard — system state, agent ops, quick control, sanctuary.*

| Trigger | Tool | Input |
|---|---|---|
| `dashboard` | `dashboard` | — |

```
dashboard
```

---

## LiveTrafficMonitor
*Monitors live network traffic, tracks packet sources, and flags anomalies.*

| Trigger | Tool | Input |
|---|---|---|
| `traffic start` | `traffic_start` | `N seconds` |
| `traffic status` | `traffic_status` | — |
| `traffic anomalies` | `traffic_anomalies` | — |

```
[TOOL:traffic_start: 30]
[TOOL:traffic_status: check]
[TOOL:traffic_anomalies: show]
```

---

## MemorySearch
*Search Trinity's sovereign memory — chat logs and vault files. Find past conversations and archived sessions by keyword.*

| Trigger | Tool | Input |
|---|---|---|
| `memory search` / `search memory` | `memory_search` | `keyword` |
| `memory read` | `memory_read` | `filename.txt` |

```
memory search canvas context overflow
memory search session 044
[TOOL:memory_read: HANDOFF_048_final.json]
```

---

## Mnemis — The Rememberer
*Tends Ethica's living memory. Indexes session digests, build logs, and vault files. Enables keyword search and deep recall across all history.*

| Trigger | Tool | Input |
|---|---|---|
| `mnemis search` | `mnemis_search` | `keyword` |
| `mnemis recall` | `mnemis_recall` | `topic / session number / vault filename` |
| `mnemis status` | `mnemis_status` | — |
| `mnemis index` | `mnemis_index` | — |

```
mnemis search WormHunter
mnemis recall session 047
mnemis status
mnemis index
```

> Mnemis watcher runs automatically — auto-indexes on session close.

---

## ModuleForge
*Drop-and-build module creator. Fill a form — Ethica builds the module, registers triggers, hot-loads. No terminal required.*

| Trigger | Tool | Input |
|---|---|---|
| `forge open` / `module forge` | `forge_open` | — |
| `forge remove` | `forge_remove` | — |

```
forge open
forge remove
```

---

## Notes — Sovereign Memory
*Plain text notes, timestamped, stored in `~/Ethica/memory/notes/`*

| Trigger | Tool | Input |
|---|---|---|
| `save note` / `take note` / `note save` | `note_save` | `your note text` |
| `list notes` / `show notes` | `note_list` | — |
| `read note` / `note read` | `note_read` | `number or keyword` |
| `delete note` | `note_delete` | `number` |

```
save note remember to test the diff tool separator
list notes
read note remember
delete note 3
```

---

## Orchestrate — The Synthesist
*Holds four minds: Dev, Critic, Expert, Hacker. Runs any problem through all four lenses and delivers a unified synthesis.*

| Trigger | Tool | Input |
|---|---|---|
| `orchestrate` / `synthesize` | `orchestrate_think` | `your question or problem` |
| `orchestrate status` | `orchestrate_status` | `check` |

```
orchestrate should I use threading or asyncio for this module
[TOOL:orchestrate_think: what's the best approach to context compression]
orchestrate status
```

> Synthesis pushed to Canvas. Council breakdown pushed to Debug tab.

---

## ProcessManager
*List, inspect, and kill system processes. Complements Guardian's filesystem watch with runtime process visibility.*

| Trigger | Tool | Input |
|---|---|---|
| `list processes` / `show processes` | `proc_list` | `name filter (optional)` |
| `kill process` | `proc_kill` | `PID or name` |
| `process info` | `proc_info` | `PID` |

```
list processes
list processes python
kill process 1234
kill process ollama
process info 1421
```

---

## Reka — The Inventor
*Systems Inventor. Brainstorms and prototypes new ideas in Canvas sandbox. Never writes to project files. Proposes, then hands off.*

| Trigger | Tool | Input |
|---|---|---|
| `reka invent` / `reka think` | `reka_invent` | `describe the idea` |
| `reka status` | `reka_status` | `check` |

```
reka invent a tool usage frequency tracker in river_state.json
reka think what would adaptive context compression look like
reka status
```

> Reka model now reads `config/settings.json` at runtime — tracks whatever model V selects in the UI.

---

## River — The Builder
*Surgical builder agent. Grep first, read exact, patch only, verify always. Never rewrites what can be patched.*

| Trigger | Tool | Input |
|---|---|---|
| `river identity` | `river_identity` | `all` |
| `river read` | `river_read` | `/path/file.py \| pattern or 10,25` |
| `river read last drop` | `river_read` | `last drop` (auto-routes images to Gage Vision) |
| `river patch` | `river_patch` | `/path/file.py \| old string \| new string` |
| `river verify` | `river_verify` | `/path/file.py` |
| `river plan` | `river_plan` | `describe the task` |
| `river run` | `river_run` | `command here` |
| `river chat` | `river_chat` | — |
| `river remember` | `river_remember` | `conversation: <note>` or `build: <note>` |
| `summarize session` | `summarize_session` | `050` |
| `river self fix` | `river_self_fix` | `/path/file.py \| old string \| new string` |
| — | `river_state_write` | `session=050 \| vault_count=140 \| notes=your note` |

```
river read ~/Ethica/core/chat_engine.py | _build_tool_context
river read last drop
river patch ~/Ethica/ui/ops_popup.py | old code | new code
river verify ~/Ethica/core/chat_engine.py
river plan add usage tracking to river_state.json
river run grep -n "def river_read" ~/Ethica/modules/river/river.py
river remember build: fixed ops_popup hyperlink Unicode offset bug
summarize session 050
river self fix ~/Ethica/ui/ops_popup.py | old | new
```

> `river read last drop` — reads `last_drop_path` from `river_state.json`. Image extensions auto-route to Gage Vision.
> `river self fix` — snapshots before patching, auto-rolls back if `ast.parse` fails. Keeps last 5 generations.

---

## SystemInfo
*Ecosystem heartbeat. Machine awareness — CPU, RAM, disk, processes, network, Ollama status.*

| Trigger | Tool | Input |
|---|---|---|
| `system status` / `system info` | `sysinfo_status` | — |
| `system memory` | `sysinfo_memory` | — |
| `system disk` | `sysinfo_disk` | — |
| `system procs` | `sysinfo_procs` | — |
| `system network` | `sysinfo_network` | — |

```
system status
system memory
system disk
system procs
system network
```

---

## TrinityDLP — Data Loss Prevention
*Scans files for sensitive data patterns, monitors file integrity, auto-recovery.*

| Trigger | Tool | Input |
|---|---|---|
| `dlp status` | `dlp_status` | — |
| `dlp scan` | `dlp_scan` | `/path/to/file` |
| `dlp hash` | `dlp_hash` | `/path/to/file` |

```
dlp status
dlp scan /home/trinity/Ethica/config/settings.json
dlp hash /home/trinity/Ethica/core/chat_engine.py
```

---

## TrinityDSE — Data Security Encryption
*AES-256, RSA-4096, post-quantum crypto (Kyber), MFA, secure SQLite, key rotation.*

| Trigger | Tool | Input |
|---|---|---|
| `dse status` | `dse_status` | — |
| `dse register` | `dse_register` | `username\|password\|role` |
| `dse rotate` | `dse_rotate_keys` | — |

```
dse status
dse register victory|mypassword|admin
dse rotate
```

---

## TrinityFirewall — AI Firewall & Intrusion Prevention
*Monitors network traffic, blocks IPs, detects port scans. Requires root for live sniffing.*

| Trigger | Tool | Input |
|---|---|---|
| `firewall start` | `firewall_start` | — |
| `firewall status` | `firewall_status` | — |
| `firewall log` | `firewall_read_log` | `last N entries` |
| `firewall block` | `firewall_block_ip` | `IP address` |
| `firewall unblock` | `firewall_unblock_ip` | `IP address` |

```
firewall start
firewall status
firewall log
firewall block 192.168.1.100
firewall unblock 192.168.1.100
```

---

## TrinityScanner — Folder Scanner
*Recursive directory scanner — timestamped JSON reports saved to `~/Ethica/scans/`*

| Trigger | Tool | Input |
|---|---|---|
| `scanner scan` | `scanner_scan` | `/path/to/folder` |
| `scanner depth` | `scanner_scan_depth` | `/path/to/folder\|depth` |
| `scanner last` / `scanner status` | `scanner_last` | — |

```
scanner scan /home/trinity/Ethica
scanner depth /home/trinity/Ethica|3
scanner last
```

---

## TrinitySIEM — Security Information & Event Management
*Real-time threat detection, anomaly analysis, automated incident response.*

| Trigger | Tool | Input |
|---|---|---|
| `siem status` | `siem_status` | — |
| `siem log` | `siem_read_log` | `last N entries` |
| `siem ingest` | `siem_ingest` | `source\|message` |

```
siem status
siem log
siem ingest firewall|suspicious connection from 192.168.1.50
```

---

## VIVARIUM — Heartbeat Dashboard
*Sovereign process monitor. Discovers running processes — nothing hardcoded. Pushes live snapshots to Canvas VIVARIUM tab.*

| Trigger | Tool | Input |
|---|---|---|
| `vivarium status` | `vivarium_status` | — |
| `vivarium start` | `vivarium_start` | `seconds (optional, default 10)` |
| `vivarium stop` | `vivarium_stop` | — |
| `vivarium watch` | `vivarium_watch` | `show` or `label=X pattern=Y` |

```
vivarium status
vivarium start 30
vivarium stop
vivarium watch show
vivarium watch label=Ollama pattern=ollama
vivarium watch label=Ethica pattern=python3
```

> Custom watch config: `~/Ethica/memory/vivarium_watch.json`
> Format: `[{"label": "MyApp", "pattern": "myapp"}]`

---

## VulnerabilityDetection
*Scans open ports and protocols for known vulnerabilities.*

| Trigger | Tool | Input |
|---|---|---|
| `vuln scan` | `vuln_scan` | — |
| `vuln protocols` | `vuln_protocols` | — |
| `vuln status` | `vuln_status` | — |

```
[TOOL:vuln_scan: run]
[TOOL:vuln_protocols: check]
[TOOL:vuln_status: show]
```

---

## WebSearch — Sovereign Web Search
*DuckDuckGo search, page fetch, news — no API key required.*

| Trigger | Tool | Input |
|---|---|---|
| `search for` / `web search` | `web_search` | `query` |
| `web fetch` / `fetch url` | `web_fetch` | `URL` |
| `search news` / `latest news` / `news on` | `web_news` | `query` |

```
search for sovereign AI architecture
web fetch https://example.com
latest news AI
news on debian 12
```

---

## WormBot — Multi-Language Code Analyzer
*Python / JS / CSS / HTML / JSON / Markdown auto-fix ON. Rust scan-only — User reviews.*

| Trigger | Tool | Input |
|---|---|---|
| Drop file | `wormbot_scan` | auto (drop zone) |
| — | `wormbot_fix` | `language\|code` |
| — | `wormbot_scan` | `/path/to/file.ext` |
| — | `wormbot_diff` | `last` |
| — | `wormbot_report` | `summary` |
| — | `wormbot_apply` | `/path/to/file.rs` |

```
[TOOL:wormbot_fix: python|def foo(): pass]
[TOOL:wormbot_scan: /home/trinity/Ethica/core/chat_engine.py]
[TOOL:wormbot_diff: last]
[TOOL:wormbot_report: summary]
[TOOL:wormbot_apply: /path/to/fixed.rs]
```

> Drop any `.py .js .css .html .json .md .sh` file onto the drop zone — WormBot scans instantly.

---

## Canvas Push Syntax
*For Ethica or modules to push content to the Living Canvas*

```
[CANVAS:TabName: content here]
[DEBUG:TabName:lang: code here]
[PROJECT: task one
task two]
[PROJECT:SprintName: task list]
[SKETCH: annotation text]
```

---

## Quick Reference Card

```
── Agents ──────────────────────────────────────────────────────
river read / patch / verify / plan / run / chat / remember
river read last drop                    ← image → Gage Vision auto
gage status / chat / read / vision
reka invent / think / status
orchestrate <problem>
mnemis search / recall / status / index
jarvis status / setup / update / search / audit
dashboard

── Security ────────────────────────────────────────────────────
guardian start / stop / status / log / reflect / trigger
firewall start / status / log / block / unblock
siem status / log / ingest
dlp status / scan / hash
dse status / register / rotate
vuln scan / protocols / status
traffic start / status / anomalies
anomaly status / train / scan

── Code & Files ────────────────────────────────────────────────
worm status / feed / broken / hunt
json fix <file>
worm fix json
diff files ~/a > ~/b
diff dirs ~/dir1 > ~/dir2
list files / file tree / read file / copy file / delete file
git status / log / diff / branch
depchecker scan / report
debugtron analyze / run / verify / status

── System ──────────────────────────────────────────────────────
system status / memory / disk / procs / network
vivarium status / start / stop / watch
list processes / kill process / process info
scanner scan / depth / last
crash status / log / clear
guard status / seal / verify / heal

── Memory & Notes ──────────────────────────────────────────────
save note / list notes / read note / delete note
memory search / memory read
memory status / edit / reflect / reset
distill run / status
summarize session <N>

── Build ────────────────────────────────────────────────────────
forge open / forge remove
web search / web fetch / news on
voice list / select / record / status
```

---

## Dev Note — Adding New Modules
When adding a new module, triggers must be registered in **two places** in `chat_engine.py`:

1. **`MODULE_TRIGGERS` dict** — maps trigger phrase → `(tool_name, default_input)`
2. **`is_tool_trigger()` method** — the `_triggers` list that routes to Ops vs chat bubble

Missing either registration causes silent failure — tool won't fire (#1) or routes to chat instead of Ops (#2).

New modules also require:
- Folder + `manifest.json` + tool file in `modules/`
- Folder name added to `MODULE_DIRS` in `ethica_guard.py`
- Manifest `tools` field must be **list of dicts** with `name` field — not plain strings

---
*Drop any supported file onto the scroll drop zone — WormBot picks it up automatically.*
*Ethica v0.1 — Walks Beside — Free Always — Built by Victory ⟁Σ∿∞*
