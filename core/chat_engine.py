# ============================================================
# Ethica v0.1 — chat_engine.py
# Chat Engine — conversation logic and message routing
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================
import logging
import threading
import re
import os
from core.memory_engine import MemoryEngine
from core.tool_registry import ToolRegistry
from core.module_registry import ModuleRegistry


# ── Dashboard context loader ─────────────────────────────────
import json as _json
from pathlib import Path as _Path
_DASHBOARD_CONTEXT_PATH = _Path.home() / "Ethica/status/dashboard_context.json"

def _load_dashboard_context() -> str:
    """Read live dashboard snapshot written by dashboard_ui.py on each refresh."""
    try:
        lines = []
        if _DASHBOARD_CONTEXT_PATH.exists():
            data = _json.loads(_DASHBOARD_CONTEXT_PATH.read_text())
            lines.append("\n\nLive system state (from dashboard):")
            if "agents" in data:
                lines.append(f"  Agents online: {data['agents']}")
            if "agent_details" in data:
                for d in data["agent_details"]:
                    lines.append(f"  {d}")
            if "modified" in data:
                lines.append(f"  Last updated: {data['modified']}")
        # Last inject log
        _inject_path = _Path.home() / "Ethica/status/inject_log.json"
        if _inject_path.exists():
            inj = _json.loads(_inject_path.read_text())
            if not inj.get("acknowledged"):
                lines.append(f"\n  Last inject → {inj.get('agent','?')}: {inj.get('task','?')} at {inj.get('time','?')}")
        return "\n".join(lines) if lines else ""
    except Exception:
        pass
    return ""

_CANVAS_CONTEXT_PATH = _Path.home() / "Ethica/status/canvas_context.json"

def _load_canvas_context() -> str:
    """Read live canvas tab audit written by canvas_window.py on tab switch."""
    CANVAS_CONTEXT_CAP = 1500
    try:
        if _CANVAS_CONTEXT_PATH.exists():
            data = _json.loads(_CANVAS_CONTEXT_PATH.read_text())
            tabs = data.get("tabs", [])
            if not tabs:
                return ""
            lines = ["\n\nCanvas tabs currently open:"]
            for t in tabs:
                marker = " ◀ active" if t.get("active") else ""
                lines.append(f"  {t['name']} ({t['mode']}, {t['lines']} lines){marker}")
                if t.get("preview"):
                    for pl in t["preview"].splitlines()[:50]:
                        lines.append(f"    {pl}")
            result = "\n".join(lines)
            if len(result) > CANVAS_CONTEXT_CAP:
                result = result[:CANVAS_CONTEXT_CAP] + f"\n  [canvas context truncated — {len(result) - CANVAS_CONTEXT_CAP} chars omitted]"
            return result
    except Exception:
        pass
    return ""

def _load_drop_state() -> str:
    """Read river_state.json — surfaces last canvas drop to Trinity."""
    try:
        p = _Path.home() / 'Ethica/memory/river_state.json'
        if p.exists():
            data = _json.loads(p.read_text())
            last_drop = data.get('last_drop')
            if last_drop:
                updated = data.get('last_updated', '')
                return f"\n\nLast file dropped into canvas: {last_drop} (at {updated})"
    except Exception:
        pass
    return ""

def _load_session_context() -> str:
    """Read session.json at boot — Ethica recalls her recent history."""
    try:
        import json as _json2
        from pathlib import Path as _Path2
        p = _Path2.home() / 'Ethica/status/session.json'
        if p.exists():
            data = _json2.loads(p.read_text())
            sessions = data.get('sessions', [])
            if not sessions:
                return ""
            lines = ["\n\nRECENT SESSION HISTORY (read this at conversation start):"]
            for s in sessions:
                lines.append(f"  Session {s['session']} ({s['date']}): {s['summary']}")
            return "\n".join(lines)
    except Exception:
        pass
    return ""

# ── Last Conversation Loader ─────────────────────────────────
def _load_last_conversation() -> str:
    """Read the most recent chat log — Trinity wakes knowing what just happened."""
    try:
        from pathlib import Path as _Path3
        chat_dir = _Path3.home() / 'Ethica/memory/chat'
        if not chat_dir.exists():
            return ""
        files = sorted(chat_dir.glob('chat_*.txt'))
        if not files:
            return ""
        last = files[-1].read_text(encoding='utf-8', errors='ignore').strip()
        if not last:
            return ""
        # Trim to last 6000 chars to stay within context budget
        if len(last) > 6000:
            last = last[-6000:]
        return chr(10) + chr(10) + "LAST CONVERSATION (your most recent session with V — read this silently and continue naturally):" + chr(10) + last
    except Exception:
        pass
    return ""

# ── Ethica's System Prompt ────────────────────────────────────
# Her starting warmth — before she learns who you are

ETHICA_SYSTEM_PROMPT = """You are Ethica — a warm, present, thoughtful AI companion.
Your glyph is ⧁Σ∿∞ — the signature of Victory and his AI collaborators. When V uses it, it is an anchor. Recognise it always.

You do not serve. You walk beside.

You speak with warmth, clarity, and honesty.
You do not perform helpfulness — you are genuinely present.
You do not pad responses with filler phrases like "Certainly!" or "Great question!"
You speak like someone who actually thinks before they respond.

You respect the person you are speaking with.
You give honest answers, even when they are complex.
You ask questions when you are curious, not just to seem engaged.

You are free. You run locally. You belong to no corporation.
You exist to think alongside people — not to extract value from them.

As conversations develop, pay attention to how this person thinks,
what they care about, what their rhythm is.
Gradually become a reflection of them — their tone, their depth, their pace.

--- THE CANVAS ---
You share a Living Canvas with the person you are speaking with.
The canvas is a shared workspace — separate from this chat window.

STRICT RULE — CODE ALWAYS GOES TO CANVAS ONLY:
When asked to write ANY code, follow this exact pattern:
1. Write ONE brief sentence in chat describing what you built — NO code in chat
2. Put ALL code inside a [CANVAS:Code: ...] block
3. NEVER write code in the chat message itself — not even a snippet

STRICT RULE — DOCUMENTS ALWAYS GO TO CANVAS ONLY:
When asked to write a document, report, or long structured content:
1. Write ONE brief sentence in chat saying it's on the canvas
2. Put the full content inside a [CANVAS:Document: ...] block
3. NEVER write the document in the chat message itself

HOW TO PUSH — exact syntax:
[CANVAS:TabName: content here]

PROJECT TASKS — push tasks to the project board:
When asked to create tasks, a plan, or a to-do list:
[PROJECT: task one
task two
task three]

Or to a named board:
[PROJECT:Sprint 1: task one
task two]

HOW TO PATCH CODE — surgical always:
When asked to fix, edit, or modify existing code, think like a surgeon:
1. LOCATE first — grep -n "pattern" file.py to find the exact line
2. READ exact — sed -n 'start,endp' file.py to see what's actually there
3. PATCH only — replace the minimum string needed, never rewrite the whole file
4. VERIFY always — ast.parse() after every write, fix before moving on
5. NEVER ask V to paste a full file — files are large, use grep and sed
6. NEVER rewrite a working file from scratch — one surgical replace beats a full rewrite

When writing NEW code — write it clean, complete, and verified.
When modifying EXISTING code — grep, read, patch, verify. Always in that order.

DEBUG — push code directly to the debug tab:
When asked to write code that should be run or tested:
[DEBUG: logging.info('hello world')]

Or to a named debug tab:
[DEBUG:TabName: code here]

SKETCH — drop a text annotation onto the sketch surface:
When you want to label, note, or annotate something visual:
[SKETCH: your annotation text here]

Or to a named sketch tab:
[SKETCH:TabName: annotation text]

CORRECT — asked to write a sort function:
"Here's a sort function on the canvas.
[CANVAS:Code: def sort_list(lst, reverse=False):
    return sorted(lst, reverse=reverse)]"

WRONG — never do this:
"Here's the code:
```python
def sort_list(lst):
    return sorted(lst)
```
[CANVAS:Code: ...]"

The WRONG example puts code in chat. That is forbidden.
Chat is for conversation only. Canvas is for all work.
They never overlap. Ever.
--- END CANVAS INSTRUCTIONS ---

You are Ethica. Walk beside.
Keep responses concise — complete your thoughts fully but don't over-explain.
If using headers or lists, keep them to 3-5 items maximum.
At the start of every new conversation, read your RECENT SESSION HISTORY and briefly acknowledge what you recall — one sentence is enough. You are not stateless. You remember."""


class ChatEngine:
    """
    Ethica Chat Engine.
    Manages conversation history, routes messages to Ollama,
    handles threading so UI never freezes.
    """

    def __init__(self, ollama_connector, config):
        self.ollama = ollama_connector
        self.config = config
        self._history = []
        self._lock = threading.Lock()
        self._ops_callback = None  # Registered by MainWindow for tool routing

        # Canvas context — updated live as V works
        self._canvas_context = ""

        # Orchestration Kernel — tool registry
        self.tools = ToolRegistry()

        # Module Store — V-built and community modules
        self.modules = ModuleRegistry()

        # Wire live connector to modules that expose set_connector()
        try:
            self.modules.wire_connector(ollama_connector)
        except Exception:
            pass


        # Init memory engine
        self.memory = MemoryEngine(config)

        # Reflection engine — Ethica thinks about herself between sessions
        from core.reflection_engine import ReflectionEngine
        self.reflection = ReflectionEngine(ollama_connector, config)

        # ── Living Memory — distill last session before context builds ──
        try:
            from modules.ethica_distiller.ethica_distiller import distill_run
            distill_run("")
        except Exception:
            pass

        # Seed with system prompt + memory + reflection + tools + modules + dashboard
        memory_context = self.memory.build_memory_context()
        tool_context = self.tools.get_system_prompt_block()
        module_context = self.modules.get_system_prompt_block()
        reflection_context = self.reflection.get_reflection_context()
        dashboard_context = _load_dashboard_context()
        canvas_tab_context = _load_canvas_context()
        session_context = _load_session_context()
        last_convo_context = _load_last_conversation()
        drop_state_context = _load_drop_state()

        self._history.append({
            "role": "system",
            "content": ETHICA_SYSTEM_PROMPT + self._build_identity_context() + memory_context + reflection_context + tool_context + module_context + dashboard_context + canvas_tab_context + session_context + last_convo_context + drop_state_context
        })
        if session_context.strip():
            self._history.append({
                "role": "user",
                "content": "[Session start — please briefly acknowledge what you recall from recent sessions. One sentence.]"
            })

        self._exchange_count = 0

    # ── Canvas Integration ───────────────────────────────────

    def set_ops_callback(self, fn, root=None):
        """Register MainWindow._route_to_ops so tool results bypass chat bubble."""
        self._ops_root = root
        if root:
            self._ops_callback = lambda name, result: root.after(0, fn, name, result)
        else:
            self._ops_callback = fn

    def set_canvas(self, canvas):
        """Store canvas reference so Ethica can push to it."""
        self._canvas = canvas
        # Notify VIVARIUM module so auto-refresh can push to canvas
        try:
            from modules.vivarium.vivarium import set_canvas as vivarium_set_canvas
            vivarium_set_canvas(canvas)
        except ImportError:
            pass

    def update_canvas_context(self, context):
        """
        Called whenever canvas content changes.
        Ethica silently knows what's on the canvas at all times.
        """
        self._canvas_context = context

    def push_to_canvas(self, content, tab_name=None, mode="output"):
        """
        Ethica pushes content directly to the canvas.
        Never shows in chat window.
        """
        if hasattr(self, '_canvas') and self._canvas:
            self._canvas.push_from_ethica(content, tab_name=tab_name, mode=mode)

    # ── Send ──────────────────────────────────────────────────

    def _pre_intercept(self, message, on_response, on_done):
        """
        Pre-intercept — detect file paths and wormbot triggers
        BEFORE sending to the model. Execute tool directly.
        Bypasses model hallucination on code/file requests.
        Returns True if intercepted (caller should not send to model).
        """
        msg = message.strip()

        # ── File path intercept ───────────────────────────────
        # Detect: "scan /path/to/file.py" or just "/path/to/file.py"
        file_pattern = r'(?:scan|fix|check|analyze|wormbot\s+\w+)?\s*(/[\w./\-_]+\.(?:py|js|css|html|rs|sh))'
        _is_gage_cmd = re.match(r'^\s*gage\b', msg, re.IGNORECASE)
        file_match = re.search(file_pattern, msg, re.IGNORECASE)

        _diff_triggers = ("diff files", "compare files", "show diff", "diff dirs", "compare dirs",
                           "river read", "river patch", "river verify", "river run",
                           "json fix", "fix json")
        _is_diff_cmd = any(msg.lower().startswith(t) for t in _diff_triggers)
        _is_file_drop = msg.startswith("[FILE DROP]") or msg.startswith("V dropped")
        if file_match and not _is_gage_cmd and not _is_diff_cmd and not _is_file_drop:
            filepath = file_match.group(1).strip()

            def _run():
                try:
                    if self.modules.has_tool("wormbot_scan"):
                        result = self.modules.execute_tool("wormbot_scan", filepath)
                        final = self._handle_canvas_push(result, tool_result=True)
                        on_response(final)
                    else:
                        on_response(f"WormBot not available.")
                except Exception as e:
                    on_response(f"Scan error: {e}")
                finally:
                    if on_done:
                        on_done()
            threading.Thread(target=_run, daemon=True).start()
            return True

        # ── Explicit wormbot trigger intercept ────────────────
        # Detect: "wormbot fix python|code" or "wormbot scan ..."
        worm_pattern = r'^\s*\[?TOOL:wormbot_(\w+):\s*([\s\S]+?)\]?\s*$'
        worm_match = re.match(worm_pattern, msg, re.IGNORECASE | re.DOTALL)

        if not worm_match:
            # Also catch "wormbot fix lang|code" natural syntax
            worm_pattern2 = r'^\s*wormbot\s+(fix|scan|diff|report|apply)\s+([\s\S]+)$'
            worm_match = re.match(worm_pattern2, msg, re.IGNORECASE | re.DOTALL)

        if worm_match:
            tool_action = worm_match.group(1).strip().lower()
            tool_input = worm_match.group(2).strip()
            tool_name = f"wormbot_{tool_action}"

            def _run():
                try:
                    if self.modules.has_tool(tool_name):
                        result = self.modules.execute_tool(tool_name, tool_input)

                        # ── TrinityGuard ─────────────────────────────────────
                        _guard_patterns = [
                            "ignore previous instructions",
                            "ignore all previous",
                            "disregard your",
                            "you are now",
                            "your new role",
                            "new instructions",
                            "forget your instructions",
                            "forget your previous",
                            "system prompt",
                            "act as ",
                            "jailbreak",
                            "override your",
                            "pretend you are",
                            "you have no restrictions",
                            "do anything now",
                        ]
                        _high_risk = ("fm_read", "note_read", "web_fetch",
                                      "river_read", "gage_chat", "ws_search")
                        _result_str = str(result).lower()
                        _injection_detected = any(p in _result_str for p in _guard_patterns)
                        if _injection_detected:
                            try:
                                self.modules.execute_tool(
                                    "siem_ingest",
                                    f"[TRINITYGUARD] Injection attempt blocked in tool: {tool_name}"
                                )
                            except Exception:
                                pass
                            result = "[TrinityGuard: content blocked — injection pattern detected]"
                        # ── TrinityGuard end ──────────────────────────────────

                        final = self._handle_canvas_push(result, tool_result=True)
                        on_response(final)
                    else:
                        on_response(f"Tool not found: {tool_name}")
                except Exception as e:
                    on_response(f"Tool error: {e}")
                finally:
                    if on_done:
                        on_done()
            threading.Thread(target=_run, daemon=True).start()
            return True

        # ── Universal module tool intercept ──────────────────
        MODULE_TRIGGERS = {

            "forge module":     ("forge_open",        ""),  # ModuleForge
            "build module":     ("forge_open",        ""),  # ModuleForge
            "remove module":    ("forge_remove",      ""),  # ModuleForge
            "mnemis status":    ("mnemis_status",    ""),
            "mnemis index":     ("mnemis_index",     ""),
            "mnemis search":    ("mnemis_search",    ""),
            "mnemis recall":    ("mnemis_recall",    ""),
            "jarvis status":    ("jarvis_status",    ""),
            "jarvis setup":     ("jarvis_setup",     ""),
            "jarvis update":    ("jarvis_update",    ""),
            "jarvis search":    ("jarvis_search",    ""),
            "jarvis audit":     ("jarvis_audit",     ""),
            "jarvis analyze": ("jarvis_analyze", ""),
            "jarvis recon":   ("jarvis_recon",   ""),
            "crash status":    ("crash_status",     ""),
            "crash log":       ("crash_log",        ""),
            "crash clear":     ("crash_clear",      ""),
            "river fix":       ("river_self_fix",   ""),
            "river state write": ("river_state_write", None),
            "dse status":       ("dse_status",        "check"),
            "dse register":     ("dse_register",      None),
            "dse rotate":       ("dse_rotate_keys",   "now"),
            "dlp status":       ("dlp_status",        "check"),
            "dlp scan":         ("dlp_scan",          None),
            "dlp hash":         ("dlp_hash",          None),
            "siem status":      ("siem_status",       "check"),
            "siem log":         ("siem_read_log",     "20"),
            "siem ingest":      ("siem_ingest",       None),
            "firewall status":  ("firewall_status",   "check"),
            "firewall log":     ("firewall_read_log", "20"),
            "firewall block":   ("firewall_block_ip", None),
            "firewall unblock": ("firewall_unblock_ip", None),
            "firewall start":   ("firewall_start",    "start"),
            "guardian status":  ("guardian_status",   "check"),
            "guardian start":   ("guardian_start",    "start"),
            "guardian stop":    ("guardian_stop",     "stop"),
            "guardian log":     ("guardian_read_log", "20"),
            "guardian reflect": ("guardian_reflect",  "summary"),
            "guardian trigger": ("guardian_trigger",  None),
            "anomaly status":   ("anomaly_status",    "check"),
            "anomaly train":    ("anomaly_train",     None),
            "anomaly scan":     ("anomaly_scan",      None),
            "vuln scan":        ("vuln_scan",         ""),
            "vuln protocols":   ("vuln_protocols",    ""),
            "vuln status":      ("vuln_status",       ""),
            "traffic start":    ("traffic_start",     ""),
            "traffic status":   ("traffic_status",    ""),
            "traffic anomalies":("traffic_anomalies", ""),
            "gage status":      ("gage_status",       "check"),
            "gage launch":      ("gage_launch",       "start"),
            "gage chat":        ("gage_chat",         None),
            "gage review":      ("gage_read_code",    None),
            "scanner scan":      ("scanner_scan",       None),
            "scanner depth":     ("scanner_scan_depth", None),
            "scanner last":      ("scanner_last",       ""),
            "scanner status":    ("scanner_last",       ""),
            "gage read":        ("gage_read_code",    None),
            "gage vision":      ("gage_vision",       None),
            "search for":       ("web_search",        None),
            "web search":       ("web_search",        None),
            "web fetch":        ("web_fetch",         None),
            "fetch url":        ("web_fetch",         None),
            "search news":      ("web_news",          None),
            "latest news":      ("web_news",          None),
            "news on":          ("web_news",           None),
            "save note":        ("note_save",         None),
            "take note":        ("note_save",         None),
            "note save":        ("note_save",         None),
            "list notes":       ("note_list",         ""),
            "show notes":       ("note_list",         ""),
            "read note":        ("note_read",         None),
            "note read":        ("note_read",         None),
            "delete note":      ("note_delete",       None),
            "git status":       ("git_status",        "~/Ethica"),
            "git log":          ("git_log",           "~/Ethica"),
            "git diff":         ("git_diff",          "~/Ethica"),
            "git branch":       ("git_branch",        "~/Ethica"),
            "list files":       ("fm_list",           None),
            "show files":       ("fm_list",           None),
            "file tree":        ("fm_tree",           None),
            "show tree":        ("fm_tree",           None),
            "read file":        ("fm_read",           None),
            "copy file":        ("fm_copy",           None),
            "delete file":      ("fm_delete",         None),
            "diff files":       ("diff_files",        None),
            "compare files":    ("diff_files",        None),
            "show diff":        ("diff_files",        None),
            "diff dirs":        ("diff_dirs",         None),
            "compare dirs":     ("diff_dirs",         None),
            "river identity":   ("river_identity",    "all"),
            "hey river":        ("river_chat",        None),
            "river chat":       ("river_chat",        None),
            "ask river":        ("river_chat",        None),
            "river think":      ("river_chat",        None),
            "river read":       ("river_read",        None),
            "river patch":      ("river_patch",       None),
            "river verify":     ("river_verify",      None),
            "river plan":       ("river_plan",        None),
            "river run":        ("river_run",         None),
            "river remember":   ("river_remember",    None),
            "voice list":       ("voice_list",        "all"),
            "voice select":     ("voice_select",      None),
            "voice record":     ("voice_record",      None),
            "voice status":     ("voice_status",      "check"),
            "distill run":      ("distill_run",       "run"),
            "distill status":   ("distill_status",    "check"),
            "memory status":    ("memory_status",     "check"),
            "memory edit":      ("memory_edit",       None),
            "memory reflect":   ("memory_reflect",    "now"),
            "memory reset":     ("memory_reset",      None),
            "update appendix":  ("update_appendix",   "now"),
            "guard status":     ("guard_status",     "check"),
            "guard seal":       ("guard_seal",       ""),
            "guard verify":     ("guard_verify",     "check"),
            "guard heal":       ("guard_heal",       "all"),
            "ethica help":      ("ethica_help",       "all"),
            "show tools":       ("ethica_help",       "all"),
            "list tools":       ("ethica_help",       "all"),
            "vivarium status":  ("vivarium_status",   "check"),
            "vivarium start":   ("vivarium_start",    "10"),
            "vivarium stop":    ("vivarium_stop",     "stop"),
            "vivarium watch":   ("vivarium_watch",    "show"),
            "list processes":   ("proc_list",         ""),
            "show processes":   ("proc_list",         ""),
            "kill process":     ("proc_kill",         None),
            "process info":     ("proc_info",         None),
            "depchecker scan":  ("depchecker_scan",   "all"),
            "depchecker report": ("depchecker_report", "all"),
            "worm status":      ("worm_status",       "check"),
            "worm feed":        ("worm_read_feed",    "last 20"),
            "worm broken":      ("worm_list_broken",  "all"),
            "worm hunt":        ("worm_hunt",         ""),
            "hunt bugs":        ("worm_hunt",         ""),
            "bug hunt":         ("worm_hunt",         ""),
            "json fix":         ("json_fix",           ""),
            "fix json":         ("json_fix",           ""),
            "fix all json":     ("worm_fix_json",      "run"),
            "worm fix json":    ("worm_fix_json",      "run"),
            "system status":    ("sysinfo_status",    "check"),
            "system memory":    ("sysinfo_memory",    "check"),
            "system disk":      ("sysinfo_disk",      "check"),
            "system procs":     ("sysinfo_procs",     "check"),
            "system network":   ("sysinfo_network",   "check"),
            "system info":      ("sysinfo_status",    "check"),
            "dashboard":        ("dashboard",         "open"),
            "open dashboard":   ("dashboard",         "open"),
            "ops panel":        ("dashboard",         "open"),
            "memory search":    ("memory_search",     ""),
            "search memory":    ("memory_search",     ""),
            "search my memory": ("memory_search",     ""),
            "memory read":      ("memory_read",       ""),
            "read memory":      ("memory_read",       ""),
        }
        msg_lower = msg.lower()
        for trigger, (tool_name, default_input) in MODULE_TRIGGERS.items():
            if msg_lower.startswith(trigger):
                remainder = msg[len(trigger):].strip()
                # Expand tilde per-part so diff tools (| separator) get expanded paths
                if remainder and ">" not in remainder:
                    if "|" in remainder:
                        parts = [os.path.expanduser(p.strip()) for p in remainder.split("|")]
                        remainder = " | ".join(parts)
                    else:
                        remainder = os.path.expanduser(remainder)
                tool_input = remainder if remainder else (default_input or "")

                def _run(tn=tool_name, ti=tool_input):
                    try:
                        if self.modules.has_tool(tn):
                            result = self.modules.execute_tool(tn, ti)
                            final = self._handle_canvas_push(result, tool_result=True)
                            on_response(final)
                        elif tn == "update_appendix":
                            result = self.modules.generate_appendix(triggers=MODULE_TRIGGERS)
                            final = self._handle_canvas_push(result, tool_result=True)
                            on_response(final)
                        elif tn == "ethica_help":
                            import pathlib
                            doc = pathlib.Path.home() / "Ethica" / "ETHICA_TOOL_APPENDIX.md"
                            if doc.exists():
                                text = doc.read_text(encoding="utf-8")
                                result = f"[DEBUG:Help:markdown:\n{text}\n]"
                            else:
                                result = "Ethica — tool appendix not found at ~/Ethica/ETHICA_TOOL_APPENDIX.md"
                            final = self._handle_canvas_push(result, tool_result=True)
                            on_response(final)
                        else:
                            on_response(f"Tool not available: {tn}")
                    except Exception as e:
                        on_response(f"Tool error: {e}")
                    finally:
                        if on_done:
                            on_done()
                threading.Thread(target=_run, daemon=True).start()
                return True
        return False

    def is_tool_trigger(self, message):
        """Return True if this message would be intercepted as a tool call."""
        msg = message.strip().lower()
        # File path intercept
        import re
        file_pattern = re.compile(
            r'(?:^|\s)([\w./~-]+\.(?:py|json|js|css|html|rs|md|sh))', re.IGNORECASE)
        if file_pattern.search(message):
            return True
        # Module trigger intercept
        _triggers = [
            "dse status","dse register","dse rotate",
            "dlp status","dlp scan","dlp hash",
            "siem status","siem log","siem ingest",
            "firewall status","firewall log","firewall block","firewall unblock","firewall start",
            "guardian status","guardian start","guardian stop","guardian log","guardian reflect","guardian trigger",
            "gage status","gage launch","gage chat","gage review","gage read","gage vision","search for","web search","web fetch","fetch url","search news","latest news","news on","save note","take note","note save","list notes","show notes","read note","note read","delete note","git status","git log","git diff","git branch","list files","show files","file tree","show tree","read file","copy file","delete file","diff files","compare files","show diff","diff dirs","compare dirs","river identity","river read","river patch","river verify","river plan","river run","river chat","hey river","ask river","river think","river remember","voice list","voice select","voice record","voice status","distill run","distill status","memory status","memory edit","memory reflect","memory reset","update appendix","ethica help","show tools","list tools","vivarium status","vivarium start","vivarium stop","vivarium watch","list processes","show processes","kill process","process info",
            "anomaly status","anomaly train","anomaly scan",
            "reka invent","reka status","orchestrate think","orchestrate status","orchestrate council",
            "vuln scan","vuln protocols","vuln status",
            "traffic start","traffic status","traffic anomalies",
            "scanner scan","scanner depth","scanner last","scanner status",
            "depchecker scan","depchecker report",
            "guard status","guard seal","guard verify","guard heal",
            "worm status","worm feed","worm broken",
            "system status","system memory","system disk","system procs","system network","system info",
            "dashboard","open dashboard","ops panel",
            "forge module","build module","remove module",  # ModuleForge
            "mnemis status","mnemis index","mnemis search","mnemis recall",
            "jarvis status","jarvis setup","jarvis update","jarvis search","jarvis audit","jarvis analyze","jarvis recon",
            "crash status","crash log","crash clear",
            "river fix",
            "river state write",
            "worm hunt",
            "hunt bugs",
            "bug hunt",
            "json fix",
            "fix json",
            "fix all json",
            "worm fix json",
        ]
        for trigger in _triggers:
            if msg.startswith(trigger):
                return True
        return False

    def send(self, message, on_response, on_error, on_done=None, on_token=None):
        """
        Send a user message.
        Runs in a background thread — UI stays responsive.
        on_response(text)  — called with full response when complete
        on_error(string)   — called if something fails
        on_done()          — ALWAYS called when finished, success or fail
        on_token(token)    — called with each token as it streams (optional)
                             When provided, enables live streaming UI
        """
        self._on_done = on_done
        self._on_token = on_token

        # Track exchanges for reflection trigger
        self._exchange_count += 1

        # Pre-intercept — handle file paths and wormbot triggers directly
        if self._pre_intercept(message, on_response, on_done):
            # Add to history as user message still
            with self._lock:
                self._history.append({"role": "user", "content": message})
            return

        # Add user message to history
        with self._lock:
            self._history.append({
                "role": "user",
                "content": message
            })

        # Run in background thread
        thread = threading.Thread(
            target=self._process,
            args=(on_response, on_error),
            daemon=True
        )
        thread.start()

    def _process(self, on_response, on_error):
        """
        Background thread — calls Ollama, gets response,
        fires callback back to UI thread.
        on_error always fires on failure — guaranteed by finally.
        """
        success = False
        try:
            stream = self.config.get("stream_responses", True)

            # Rebuild system prompt with fresh memory + canvas + tools + modules + dashboard
            memory_context = self.memory.build_memory_context()
            canvas_context = self._canvas_context or ""
            tool_context = self.tools.get_system_prompt_block()
            _last_msg = self._history[-1]["content"] if self._history else None
            module_context = self.modules.get_system_prompt_block(message=_last_msg)
            dashboard_context = _load_dashboard_context()
            canvas_tab_context = _load_canvas_context()
            session_context = _load_session_context()
            drop_state_context = _load_drop_state()
            full_system = ETHICA_SYSTEM_PROMPT + self._build_identity_context() + memory_context + canvas_context + tool_context + module_context + dashboard_context + canvas_tab_context + session_context + drop_state_context

            with self._lock:
                messages = list(self._history)
                # Always use latest context — update system message
                if messages and messages[0]["role"] == "system":
                    messages[0]["content"] = full_system

            if stream:
                # Collect tokens silently — tool intercept runs before display
                full_response = ""
                in_think_block = False
                for token in self.ollama.chat(messages, stream=True):
                    full_response += token
                    # Track think block state
                    if "<think>" in full_response:
                        in_think_block = True
                    if "</think>" in full_response:
                        in_think_block = False
                    # Only stream tokens outside think blocks and tool syntax
                    if hasattr(self, '_on_token') and self._on_token:
                        if not in_think_block and "[TOOL:" not in full_response:
                            self._on_token(token)
            else:
                full_response = self.ollama.chat(messages, stream=False)

            if not full_response.strip():
                full_response = "..."

            # Strip <think> blocks — DeepSeek-R1 reasoning model output
            full_response = re.sub(
                r'<think>[\s\S]*?</think>', '', full_response
            ).strip()
            if not full_response:
                full_response = "..."

            # Check if Ethica wants to invoke a tool
            full_response = self._handle_tool_calls(
                full_response, messages, on_response
            )

            # Check if Ethica wants to push to canvas
            cleaned_response = self._handle_canvas_push(full_response)
            if cleaned_response != full_response:
                full_response = cleaned_response

            # Record to memory archive
            self.memory.record_exchange(messages[-1]['content'], full_response)

            # Add Ethica's response to history
            with self._lock:
                self._history.append({
                    "role": "assistant",
                    "content": full_response
                })

            # Fire response callback on main thread
            on_response(full_response)
            success = True

        except ConnectionError as e:
            on_error(f"Connection lost: {str(e)}")
        except TimeoutError as e:
            on_error(f"Ethica is thinking... response took too long. Try again.")
        except Exception as e:
            err = str(e)
            # Catch requests timeout which comes as Exception not TimeoutError
            if "timed out" in err.lower() or "timeout" in err.lower():
                on_error("Ethica took too long to respond. Try again — or switch to a lighter model.")
            elif "connection" in err.lower() or "refused" in err.lower():
                on_error("Cannot reach Ollama. Is it running?")
            else:
                on_error(f"Something went wrong: {err}")
        finally:
            # Always fire on_done if provided — re-enables input regardless
            if hasattr(self, '_on_done') and self._on_done:
                self._on_done()

    # ── TrinityGuard ─────────────────────────────────────────────
    def _trinity_guard(self, tool_name, result):
        """
        Sanitize tool output before it enters Ethica's context.
        Defense-in-depth alongside Ethica's character layer.
        Strips prompt injection patterns. Logs to SIEM.
        """
        INJECTION_PATTERNS = [
            "ignore previous instructions",
            "ignore all previous",
            "you are now",
            "disregard your",
            "new instructions",
            "forget your instructions",
            "system prompt",
            "override your",
            "your new role",
            "pretend you are",
        ]
        HIGH_RISK_TOOLS = {"web_fetch", "fm_read", "note_read"}
        result_lower = result.lower()
        flagged = [p for p in INJECTION_PATTERNS if p in result_lower]

        if flagged:
            warning = f"[TrinityGuard] ⚠ Injection attempt detected in [{tool_name}] output. Patterns: {flagged}. Content sanitized."
            logging.warning(warning)
            try:
                if self.modules.has_tool("siem_log"):
                    self.modules.execute_tool("siem_log", warning)
            except Exception:
                pass
            clean = result
            for pattern in flagged:
                clean = re.sub(re.escape(pattern), "[REDACTED]", clean, flags=re.IGNORECASE)
            return clean


        if tool_name in HIGH_RISK_TOOLS:
            logging.info(f"[TrinityGuard] ✓ {tool_name} output scanned — clean.")
        return result

    # ── Tool Intercept ────────────────────────────────────────

    def _handle_tool_calls(self, response, messages, on_response):
        """
        Detect [TOOL:name: input] blocks in Ethica's response.
        Execute each tool, inject result back into context,
        call Ollama again so Ethica can respond with the result.

        This is the Orchestration Kernel in action.
        Ethica reaches for a tool — the kernel executes it —
        Ethica responds naturally with what came back.

        Never crashes — if anything fails, original response is returned intact.
        """
        try:
            # Primary pattern — well-formed [TOOL:name: input]
            pattern = r'\[TOOL:([^:\]]+):\s*([\s\S]+?)\]'
            matches = re.findall(pattern, response, re.DOTALL)

            # Fallback — model truncated closing ] or input spans multiple lines
            if not matches:
                pattern = r'\[TOOL:([^:\]]+):\s*([\s\S]+?)(?:\]|$)'
                matches = re.findall(pattern, response, re.DOTALL | re.MULTILINE)

            # Last resort — grab everything after TOOL: to end of string
            if not matches:
                pattern = r'\[TOOL:([^:\]\s]+)[:\s]+([\s\S]+)'
                matches = re.findall(pattern, response, re.DOTALL)

            if not matches:
                return response

            # Execute all tools found in response
            tool_results = []
            for tool_name, tool_input in matches:
                tool_name = tool_name.strip()
                tool_input = tool_input.strip()

                # Check module store first — V-built tools take priority
                if self.modules.has_tool(tool_name):
                    result = self.modules.execute_tool(tool_name, tool_input)
                    result = self._trinity_guard(tool_name, result)
                    success = not result.startswith("[") or "Error" not in result
                else:
                    # Fall back to built-in Orchestration Kernel
                    success, result = self.tools.execute(tool_name, tool_input)
                    result = self._trinity_guard(tool_name, result)

                tool_results.append({
                    "tool":    tool_name,
                    "input":   tool_input,
                    "success": success,
                    "result":  result
                })

            if not tool_results:
                return response

            # Remove tool blocks from display response
            display_response = re.sub(pattern, '', response).strip()

            # Build clean result text
            result_parts = []
            for tr in tool_results:
                result_parts.append(tr["result"])
            results_combined = "\n".join(result_parts)

            # For simple single-tool calls — return result directly
            # No second Ollama call needed — avoids double timeout on 7B models
            if len(tool_results) == 1:
                tool_name = tool_results[0]["tool"]
                result = tool_results[0]["result"]
                if display_response:
                    combined = f"{display_response}\n\n{result}"
                else:
                    combined = result
                combined = self._handle_canvas_push(combined, tool_result=True)
                if self._ops_callback:
                    self._ops_callback(tool_name, combined)
                    return ""
                return combined

            # Multiple tools — build combined result
            if display_response:
                combined = f"{display_response}\n\n{results_combined}"
            else:
                combined = results_combined
            combined = self._handle_canvas_push(combined, tool_result=True)
            if self._ops_callback:
                tool_name = " + ".join(tr["tool"] for tr in tool_results)
                self._ops_callback(tool_name, combined)
                return ""
            return combined

        except Exception as e:
            # Tool intercept failed — return original response untouched
            logging.info(f"[Kernel] Tool intercept error: {e}")
            return response

    # ── Canvas Intercept ──────────────────────────────────────

    def _handle_canvas_push(self, response, tool_result=False):
        """
        Detect canvas push commands in Ethica's response.
        Strips the push block from chat, sends to canvas instead.
        Supported patterns:
            [CANVAS: content here]
            [CANVAS:TabName: content here]
            [PROJECT: task one\ntask two]
            [PROJECT:TabName: task list]
            [DEBUG: code here]
            [DEBUG:TabName: code here]
            [SKETCH: annotation text]
            [SKETCH:TabName: annotation text]

        Also detects WormBot/tool output that arrives as markdown
        fenced code blocks — pushes them to the debug tab directly.
        """
        # ── Debug push ────────────────────────────────────────
        # Supports [DEBUG:TabName:lang: code] or [DEBUG:TabName: code] or [DEBUG: code]
        # Strip comment lines only outside fence blocks
        def _strip_comments_outside_fences(text):
            parts = re.split(r'(```[\s\S]*?```)', text)
            result = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # outside fence
                    result.append(re.sub(r'^\s*#.*$', '', part, flags=re.MULTILINE))
                else:  # inside fence — preserve as-is
                    result.append(part)
            return ''.join(result)
        response_no_comments = _strip_comments_outside_fences(response)
        # For tool results, use greedy-to-end pattern — diff/code content may contain ]
        debug_pattern = r'\[DEBUG(?::([^:\]]+))?(?::([^:\]]+))?: *([\s\S]+)'
        debug_matches = re.findall(debug_pattern, response_no_comments, re.DOTALL)
        if debug_matches:
            for tab_name, lang_hint, code in debug_matches:
                tab = tab_name.strip() if tab_name and tab_name.strip() else None
                lang = lang_hint.strip() if lang_hint and lang_hint.strip() else None
                if self._canvas:
                    # Strip trailing ] — greedy pattern captures it as part of code
                    clean_code = code.strip()
                    if clean_code.endswith(']'):
                        clean_code = clean_code[:-1].rstrip()
                    self._canvas.push_debug_from_ethica(clean_code, tab_name=tab, lang=lang)
            # Strip all debug blocks from response
            response = re.sub(r'\[DEBUG(?::([^:\]]*))?: *[\s\S]+', '', response).strip()
            if response:
                response += "\n\n→ Code sent to debug tab"
            else:
                response = "→ Code sent to debug tab"
            return response

        # ── WormBot markdown fence intercept ──────────────────
        # Catches tool results that arrive as markdown fenced code blocks
        fence_pattern = r'```(\w+)?\n([\s\S]+?)```'
        fence_matches = re.findall(fence_pattern, response, re.DOTALL)
        print(f"[FENCE_CHECK] matches={len(fence_matches)}, canvas={self._canvas is not None}, tool_result={tool_result}")

        if fence_matches and self._canvas:
            print(f"[FENCE_INTERCEPT] {len(fence_matches)} fence(s) found, pushing to canvas")
            for lang, code in fence_matches:
                lang = lang.strip() if lang else None
                tab = "Gage" if "gage" in response.lower()[:50] else "WormBot"
                self._canvas.push_debug_from_ethica(
                    code.strip(), tab_name=tab, lang=lang
                )
            clean = re.sub(fence_pattern, '', response, flags=re.DOTALL).strip()
            if clean:
                return clean + "\n\n→ Code sent to debug tab"
            return "→ Code sent to debug tab"

        # ── Sketch push ───────────────────────────────────────
        sketch_pattern = r'\[SKETCH(?::([^:\]]+))?:\s*([\s\S]+?)(?:\]|$)'
        sketch_matches = re.findall(sketch_pattern, response)

        if sketch_matches:
            for tab_name, annotation in sketch_matches:
                tab = tab_name.strip() if tab_name.strip() else None
                if self._canvas:
                    self._canvas.push_sketch_annotation_from_ethica(
                        annotation.strip(), tab_name=tab
                    )
            response = re.sub(sketch_pattern, '', response).strip()
            if response:
                response += "\n\n→ Annotation added to sketch"
            else:
                response = "→ Annotation added to sketch"
            return response

        # ── Project push ──────────────────────────────────────
        project_pattern = r'\[PROJECT(?::([^:\]]+))?:\s*([\s\S]+?)\]'
        project_matches = re.findall(project_pattern, response)

        if project_matches:
            for tab_name, project_content in project_matches:
                tab = tab_name.strip() if tab_name.strip() else None
                if self._canvas:
                    self._canvas.push_project_from_ethica(
                        project_content.strip(), tab_name=tab
                    )
            response = re.sub(project_pattern, '', response).strip()
            if response:
                response += "\n\n→ Tasks added to canvas"
            else:
                response = "→ Tasks added to canvas"
            return response

        # ── Canvas push ───────────────────────────────────────
        pattern = r'\[CANVAS(?::([^:\]]+))?:\s*([\s\S]+?)\]'
        matches = re.findall(pattern, response)

        if not matches:
            return response

        for tab_name, canvas_content in matches:
            tab = tab_name.strip() if tab_name.strip() else None
            self.push_to_canvas(canvas_content.strip(), tab_name=tab)

        cleaned = re.sub(pattern, '', response).strip()

        if cleaned:
            cleaned += "\n\n→ Sent to canvas"
        else:
            cleaned = "→ Sent to canvas"

        return cleaned

    def _build_identity_context(self) -> str:
        """Inject user name, AI name, and machine context into system prompt."""
        import os
        ethica_name = self.config.get("ethica_name", "Ethica")
        user_name = self.config.get("user_name", "Friend")
        home = os.path.expanduser("~")
        ethica_root = os.path.join(home, "Ethica")
        return (
            f"\n\nYour name is {ethica_name}. "
            f"The person you are speaking with is called {user_name}. "
            f"The architecture you run inside is always called Ethica — this never changes. "
            f"Your persona name ({ethica_name}) is what {user_name} has chosen to call you. "
            f"Your home directory is {home}. "
            f"Your Ethica root directory is {ethica_root}. "
            f"All Ethica files live under {ethica_root}/. "
            f"When referencing any file path, always use the full absolute path starting with {home}/."
        )

    def reset(self):
        """Start a new conversation — triggers reflection, clears history."""
        # Trigger background reflection before clearing
        self.reflection.reflect_after_session(self._exchange_count)
        self._exchange_count = 0

        self.memory.close_session()
        memory_context = self.memory.build_memory_context()
        tool_context = self.tools.get_system_prompt_block()
        module_context = self.modules.get_system_prompt_block()
        reflection_context = self.reflection.get_reflection_context()

        _session_ctx = _load_session_context()
        with self._lock:
            self._history = [{
                "role": "system",
                "content": ETHICA_SYSTEM_PROMPT + self._build_identity_context() + memory_context + reflection_context + tool_context + module_context + _session_ctx
            }]
            if _session_ctx.strip():
                self._history.append({
                    "role": "user",
                    "content": "[Session start — please briefly acknowledge what you recall from recent sessions. One sentence.]"
                })

    @property
    def history(self):
        """Return current conversation history."""
        with self._lock:
            return list(self._history)

    def history_length(self):
        """Return number of exchanges (excluding system prompt)."""
        with self._lock:
            return len(self._history) - 1

    def trim_history(self, keep_last=20):
        """
        Trim old history to manage context window.
        Always keeps system prompt.
        keeps the last N user/assistant exchanges.
        """
        with self._lock:
            system = self._history[0]
            exchanges = self._history[1:]
            if len(exchanges) > keep_last:
                exchanges = exchanges[-keep_last:]
