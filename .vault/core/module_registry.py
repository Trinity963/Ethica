# ============================================================
# Ethica v0.1 — module_registry.py
# Sovereign Module Store — Ethica's Extensible Tool Engine
# Architect: Victory  |  Build Partner: River aka Claude
# ⟁Σ∿∞
#
# Each module is a folder in /modules/:
#   modules/
#     wormbot/
#       manifest.json   ← identity, tools, autonomous flags
#       wormbot.py      ← implementation
#
# Drop a folder in. Restart. Ethica discovers it.
# No changes to Ethica herself. Ever.
#
# Manifest spec:
# {
#   "name": "WormBot",
#   "version": "1.0",
#   "description": "...",
#   "author": "Victory",
#   "autonomous": true,           ← can Ethica use this herself?
#   "autonomous_triggers": [...], ← keywords that make her reach for it
#   "tools": [
#     {
#       "name": "tool_name",
#       "description": "...",
#       "syntax": "[TOOL:tool_name: input]",
#       "autonomous": true,       ← per-tool autonomous flag
#       "example": "..."          ← optional usage example
#     }
#   ]
# }
# ============================================================

import os
import json
import importlib.util
import logging
from datetime import datetime


BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(BASE_DIR, "modules")


class EthicaTool:
    """A single callable tool from a module."""
    def __init__(self, name, description, syntax, autonomous,
                 example, module_name, handler):
        self.name        = name
        self.description = description
        self.syntax      = syntax
        self.autonomous  = autonomous
        self.example     = example
        self.module_name = module_name
        self.handler     = handler   # callable(input_str) -> str

    def call(self, input_str):
        """Execute this tool with the given input string."""
        try:
            result = self.handler(input_str)
            return str(result) if result is not None else "(no output)"
        except Exception as e:
            return f"[{self.name}] Error: {str(e)}"


class EthicaModule:
    """A loaded module with its manifest and tools."""
    def __init__(self, name, version, description, author,
                 autonomous, triggers, tools, loaded_at, impl=None):
        self.name        = name
        self.version     = version
        self.description = description
        self.author      = author
        self.autonomous  = autonomous   # module-level autonomous flag
        self.triggers    = triggers     # keywords that activate autonomous use
        self.tools       = tools        # list of EthicaTool
        self.loaded_at   = loaded_at
        self.impl        = impl         # loaded implementation module

    def get_tool(self, tool_name):
        for tool in self.tools:
            if tool.name.lower() == tool_name.lower():
                return tool
        return None


class ModuleRegistry:
    """
    Ethica's sovereign module store.

    Scans /modules/ at startup.
    Discovers manifests. Loads implementations.
    Injects tool syntax into Ethica's system prompt.
    Routes [TOOL:] calls to correct handlers.
    """

    def __init__(self):
        self._modules    = {}   # name → EthicaModule
        self._tool_index = {}   # tool_name → EthicaTool
        self._load_errors = []
        self._loaded_at  = None

        os.makedirs(MODULES_DIR, exist_ok=True)
        self._scan()

    # ── Discovery ─────────────────────────────────────────────

    def _scan(self):
        """Scan modules/ directory and load all valid modules."""
        self._modules    = {}
        self._tool_index = {}
        self._load_errors = []

        if not os.path.exists(MODULES_DIR):
            logging.warning("[ModuleRegistry] No modules/ directory found")
            return

        for entry in sorted(os.listdir(MODULES_DIR)):
            module_dir = os.path.join(MODULES_DIR, entry)
            if not os.path.isdir(module_dir):
                continue

            manifest_path = os.path.join(module_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                continue

            self._load_module(entry, module_dir, manifest_path)

        self._loaded_at = datetime.now().isoformat()
        count = len(self._modules)
        tools = len(self._tool_index)
        logging.info(f"[ModuleRegistry] {count} module(s) loaded, {tools} tool(s) available")

    def _load_module(self, folder_name, module_dir, manifest_path):
        """Load a single module from its folder."""
        try:
            # Read manifest
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            name        = manifest.get("name", folder_name)
            version     = manifest.get("version", "1.0")
            description = manifest.get("description", "")
            author      = manifest.get("author", "Unknown")
            autonomous  = manifest.get("autonomous", False)
            triggers    = manifest.get("autonomous_triggers", [])
            tool_defs   = manifest.get("tools", [])

            # Find implementation file — respect explicit entry in manifest
            entry     = manifest.get("entry", None)
            impl_file = self._find_impl(module_dir, folder_name, entry)

            # Load implementation module
            impl = None
            if impl_file:
                impl = self._load_impl(impl_file, folder_name)

            # Build tool objects
            tools = []
            for t in tool_defs:
                tool_name   = t.get("name", "")
                tool_desc   = t.get("description", "")
                tool_syntax = t.get("syntax", f"[TOOL:{tool_name}: input]")
                tool_auto   = t.get("autonomous", False)
                tool_example= t.get("example", "")

                # Find handler in implementation
                handler = self._find_handler(impl, tool_name)

                tool = EthicaTool(
                    name        = tool_name,
                    description = tool_desc,
                    syntax      = tool_syntax,
                    autonomous  = tool_auto,
                    example     = tool_example,
                    module_name = name,
                    handler     = handler
                )
                tools.append(tool)

                # Register in global tool index
                self._tool_index[tool_name.lower()] = tool

            module = EthicaModule(impl=impl,
                name        = name,
                version     = version,
                description = description,
                author      = author,
                autonomous  = autonomous,
                triggers    = triggers,
                tools       = tools,
                loaded_at   = datetime.now().isoformat()
            )
            self._modules[name.lower()] = module
            logging.info(f"[ModuleRegistry] ✓ {name} v{version} — {len(tools)} tool(s)")

        except Exception as e:
            err = f"[ModuleRegistry] ✗ {folder_name}: {str(e)}"
            logging.error(err)
            self._load_errors.append(err)

    def _find_impl(self, module_dir, folder_name, entry=None):
        """Find the Python implementation file.
        Respects explicit 'entry' from manifest.
        Never loads main.py — that belongs to standalone apps.
        """
        # Manifest explicitly declares entry point
        if entry:
            explicit = os.path.join(module_dir, entry)
            if os.path.exists(explicit):
                return explicit

        # Named candidates — never main.py
        candidates = [
            os.path.join(module_dir, f"{folder_name}.py"),
            os.path.join(module_dir, "module.py"),
        ]

        # Any .py that isn't main.py, __init__.py, or a test file
        SKIP = {"main.py", "__init__.py", "setup.py"}
        for f in sorted(os.listdir(module_dir)):
            if (f.endswith(".py")
                    and f not in SKIP
                    and not f.startswith("test_")):
                candidates.append(os.path.join(module_dir, f))

        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _load_impl(self, impl_file, module_name):
        """Dynamically load a Python module file."""
        try:
            spec   = importlib.util.spec_from_file_location(
                f"ethica_module_{module_name}", impl_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            logging.error(f"[ModuleRegistry] Failed to load {impl_file}: {e}")
            return None

    def wire_connector(self, connector):
        """Pass live ollama connector to any module that exposes set_connector()."""
        for module in self._modules.values():
            if module.impl and hasattr(module.impl, "set_connector"):
                try:
                    module.impl.set_connector(connector)
                except Exception:
                    pass

    def _find_handler(self, impl, tool_name):
        """Find a callable handler for a tool name in the impl module."""
        if impl is None:
            return self._make_stub_handler(tool_name)

        # Look for exact function name
        candidates = [
            tool_name,
            tool_name.replace("-", "_"),
            f"tool_{tool_name}",
            f"run_{tool_name}",
            f"handle_{tool_name}",
        ]
        for name in candidates:
            fn = getattr(impl, name, None)
            if callable(fn):
                return fn

        # Look for a generic 'run' or 'execute' function
        for name in ("run", "execute", "main", "process"):
            fn = getattr(impl, name, None)
            if callable(fn):
                return fn

        return self._make_stub_handler(tool_name)

    def _make_stub_handler(self, tool_name):
        """Return a stub handler for tools with no implementation yet."""
        def stub(input_str):
            return f"[{tool_name}] Module loaded but no handler implemented yet."
        return stub

    # ── Tool Execution ────────────────────────────────────────

    def execute_tool(self, tool_name, input_str):
        """
        Execute a tool by name.
        Called by chat_engine when [TOOL:tool_name: input] is detected.
        Returns result string.
        """
        tool = self._tool_index.get(tool_name.lower())
        if not tool:
            return None   # Not a module tool — let built-in registry handle it
        result = tool.call(input_str)
        self._increment_usage(tool_name.lower())
        return result

    def _increment_usage(self, name):
        """Increment module tool usage counter in river_state.json."""
        import json, os
        path = os.path.expanduser('~/Ethica/memory/river_state.json')
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            usage = state.setdefault('tool_usage', {})
            usage[name] = usage.get(name, 0) + 1
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass  # never break tool execution over a counter write

    def has_tool(self, tool_name):
        return tool_name.lower() in self._tool_index

    # ── Autonomous Trigger Detection ──────────────────────────

    def get_autonomous_tools_for_context(self, message):
        """
        Given a user message, return any autonomous tools whose
        triggers match — Ethica should consider using these.
        Returns list of (module, tool) pairs.
        """
        message_lower = message.lower()
        matches = []

        for module in self._modules.values():
            if not module.autonomous:
                continue
            # Check module-level triggers
            triggered = any(
                t.lower() in message_lower
                for t in module.triggers
            )
            if triggered:
                for tool in module.tools:
                    if tool.autonomous:
                        matches.append((module, tool))

        return matches

    # ── System Prompt Injection ───────────────────────────────

    # ── Keyword Router ───────────────────────────────────────
    KEYWORD_GROUPS = {
        "security":    ["Guardian", "TrinitySIEM", "TrinityFirewall", "TrinityDLP", "TrinityDSE", "VulnerabilityDetection"],
        "search":      ["WebSearch", "MemorySearch", "Mnemis"],
        "scan":        ["VulnerabilityDetection", "TrinityScanner", "AnomalyDetection", "LiveTrafficMonitor", "WormBot", "CodeWorm"],
        "worm":        ["WormBot", "CodeWorm"],
        "git":         ["GitTool"],
        "image":       ["Gage"],
        "vision":      ["Gage"],
        "code":        ["WormBot", "CodeWorm", "Debugtron", "DiffTool"],
        "debug":       ["Debugtron", "CrashReporter"],
        "file":        ["FileManager", "DiffTool"],
        "memory":      ["EthicaMemory", "Mnemis", "MemorySearch"],
        "note":        ["Notes"],
        "process":     ["ProcessManager", "VIVARIUM"],
        "system":      ["SystemInfo", "VIVARIUM", "ProcessManager"],
        "network":     ["TrinityFirewall", "LiveTrafficMonitor", "TrinitySIEM"],
        "voice":       ["EthicaVoice"],
        "river":       ["River"],
        "gage":        ["Gage"],
        "reka":        ["Reka"],
        "jarvis":      ["J.A.R.V.I.S."],
        "forge":       ["ModuleForge"],
        "distill":     ["EthicaDistiller"],
        "crash":       ["CrashReporter"],
        "guardian":    ["Guardian"],
        "firewall":    ["TrinityFirewall"],
        "vivarium":    ["VIVARIUM"],
        "anomaly":     ["AnomalyDetection"],
        "traffic":     ["LiveTrafficMonitor"],
        "vuln":        ["VulnerabilityDetection"],
        "scanner":     ["TrinityScanner"],
        "siem":        ["TrinitySIEM"],
        "dlp":         ["TrinityDLP"],
        "dse":         ["TrinityDSE"],
        "orchestrate": ["Orchestrate"],
        "diff":        ["DiffTool"],
        "depcheck":    ["DepChecker"],
        "nyxt":        ["Nyxt"],
        "browser":     ["Nyxt"],
        "recon":       ["Nyxt", "J.A.R.V.I.S."],
        "open":        ["Nyxt"],
        "zip":         ["FileManager"],
        "unzip":       ["FileManager"],
        "archive":     ["FileManager"],
        "extract":     ["FileManager"],
    }

    def _get_active_modules(self, message=None):
        """
        Return set of module names to include in prompt.
        Keyword match + top 8 by usage. Falls back to all if no match.
        """
        import json, os
        all_names = set(m.name for m in self._modules.values())
        if not message:
            return all_names

        msg_lower = message.lower()
        matched = set()

        for keyword, module_names in self.KEYWORD_GROUPS.items():
            if keyword in msg_lower:
                matched.update(module_names)

        # Top N by usage from river_state.json
        try:
            path = os.path.expanduser("~/Ethica/memory/river_state.json")
            with open(path, "r") as f:
                state = json.load(f)
            usage = state.get("tool_usage", {})
            module_usage = {}
            for tool_name, count in usage.items():
                tool = self._tool_index.get(tool_name.lower())
                if tool:
                    mn = getattr(tool, "module_name", None)
                    if mn:
                        module_usage[mn] = module_usage.get(mn, 0) + count
            top = sorted(module_usage, key=lambda k: module_usage[k], reverse=True)[:8]
            matched.update(top)
        except Exception:
            pass

        # Always include core
        matched.update(["River", "kernel", "EthicaGuard"])

        # Safe fallback — if only core matched, return all
        core = {"River", "kernel", "EthicaGuard"}
        return matched if matched - core else all_names

    def get_system_prompt_block(self, message=None):
        """
        Build the system prompt block for all loaded module tools.
        Adaptive — filters by keyword match and usage when message provided.
        Falls back to full block if no message or no matches.
        """
        if not self._modules:
            return ""

        active = self._get_active_modules(message)
        modules_to_show = [m for m in self._modules.values() if m.name in active]

        lines = ["\n--- INSTALLED MODULES ---"]
        lines.append("You have access to the following installed modules and tools.\n")

        # TrinityGuard budget: keep module block under 2400 chars
        _budget = 2400
        _compact = False
        _test_lines = []
        for module in modules_to_show:
            _test_lines.append(f"MODULE: {module.name} v{module.version}")
            _test_lines.append(f"  {module.description}")
            for tool in module.tools:
                auto_note = " [auto]" if tool.autonomous else " [manual]"
                _test_lines.append(f"    {tool.syntax}{auto_note}")
                _test_lines.append(f"      -> {tool.description}")
        if len("\n".join(_test_lines)) > _budget:
            _compact = True

        for module in modules_to_show:
            lines.append(f"MODULE: {module.name} v{module.version}")
            if not _compact:
                lines.append(f"  {module.description}")
            if module.autonomous and module.triggers:
                trigger_str = ", ".join(f'"{t}"' for t in module.triggers[:2])
                lines.append(f"  Triggers: {trigger_str}")
            lines.append("  Tools:")
            for tool in module.tools:
                auto_note = " [auto]" if tool.autonomous else " [manual]"
                if _compact:
                    lines.append(f"    {tool.syntax}{auto_note}")
                else:
                    lines.append(f"    {tool.syntax}{auto_note}")
                    lines.append(f"      -> {tool.description}")
            lines.append("")

        lines.append(
            "Use [auto] tools autonomously when triggers match. "
            "Use [manual] tools only when explicitly requested. "
            "Always use exact syntax shown above."
        )
        lines.append("--- END MODULES ---")
        return "\n".join(lines)

        return "\n".join(lines)

    # ── Introspection ─────────────────────────────────────────

    def list_modules(self):
        """Return list of loaded module summaries."""
        return [
            {
                "name":       m.name,
                "version":    m.version,
                "description":m.description,
                "author":     m.author,
                "autonomous": m.autonomous,
                "tool_count": len(m.tools),
                "tools":      [t.name for t in m.tools],
                "enabled":    getattr(m, "enabled", True)
            }
            for m in self._modules.values()
        ]

    def set_enabled(self, name, enabled):
        """Enable or disable a module by name."""
        if name in self._modules:
            self._modules[name].enabled = enabled
            # Remove or restore tools from index
            mod = self._modules[name]
            if not enabled:
                for tool in mod.tools:
                    self._tool_index.pop(tool.name, None)
            else:
                for tool in mod.tools:
                    self._tool_index[tool.name] = tool
            logging.info(f"[ModuleRegistry] {'✓' if enabled else '✗'} {name} {'enabled' if enabled else 'disabled'}")

    def reload(self):
        """Reload all modules from disk."""
        logging.info("[ModuleRegistry] Reloading all modules...")
        self._modules.clear()
        self._tool_index.clear()
        self._load_all()
        logging.info(f"[ModuleRegistry] Reload complete — {len(self._modules)} module(s) loaded")

    def list_tools(self):
        """Return all available tools across all modules."""
        return [
            {
                "name":       t.name,
                "module":     t.module_name,
                "description":t.description,
                "syntax":     t.syntax,
                "autonomous": t.autonomous
            }
            for t in self._tool_index.values()
        ]

    def register_module(self, folder_path):
        """Hot-load a single module from an absolute folder path."""
        import os
        folder_path = os.path.expanduser(folder_path.strip())
        if not os.path.isdir(folder_path):
            return f"[ModuleRegistry] Not a directory: {folder_path}"
        manifest_path = os.path.join(folder_path, "manifest.json")
        if not os.path.exists(manifest_path):
            return f"[ModuleRegistry] No manifest.json in: {folder_path}"
        folder_name = os.path.basename(folder_path)
        # Unload existing module with same folder name if present
        existing = [k for k, m in self._modules.items()
                    if os.path.basename(folder_path) in k or k in folder_name.lower()]
        for k in existing:
            mod = self._modules.pop(k, None)
            if mod:
                for tool in mod.tools:
                    self._tool_index.pop(tool.name.lower(), None)
        prev_count = len(self._modules)
        self._load_module(folder_name, folder_path, manifest_path)
        if len(self._modules) > prev_count:
            name = list(self._modules.values())[-1].name
            tools = len(list(self._modules.values())[-1].tools)
            return f"[ModuleRegistry] ✓ {name} loaded — {tools} tool(s) active"
        return f"[ModuleRegistry] ✗ Failed to load module from: {folder_path}"

    def get_status(self):
        return {
            "modules":     len(self._modules),
            "tools":       len(self._tool_index),
            "loaded_at":   self._loaded_at,
            "errors":      self._load_errors,
            "module_list": self.list_modules()
        }
    def generate_appendix(self, triggers=None):
        """
        Auto-generate ETHICA_TOOL_APPENDIX.md from loaded manifests.
        Static sections (Canvas Push Syntax, Dev Note) are baked in.
        Called by 'update appendix' trigger or manually.
        triggers — MODULE_TRIGGERS dict from chat_engine, optional.
        """
        from datetime import datetime
        import os

        # Build reverse lookup: tool_name -> [trigger phrases]
        trigger_map = {}
        if triggers:
            for phrase, (tool_name, _) in triggers.items():
                trigger_map.setdefault(tool_name, []).append(phrase)

        now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mod_count = len(self._modules)
        tool_count = len(self._tool_index)

        lines = [
            "# Ethica — Tool Appendix",
            "### Complete Module & Trigger Reference",
            "**Architect**: Victory — The Architect | ⟁Σ∿∞",
            f"**Version**: Ethica v0.1 | Updated: {now}",
            f"**Modules**: {mod_count} | **Tools**: {tool_count}",
            "",
            "---",
            "",
            "## How to Call Tools",
            "",
            "Two ways to invoke any tool:",
            "",
            "**1. Natural language trigger** (typed in chat — instant, no model)",
            "```",
            "guardian start",
            "scanner scan /home/trinity/Ethica",
            "worm status",
            "```",
            "",
            "**2. Direct tool syntax** (for use in Ethica's system or by modules)",
            "```",
            "[TOOL:tool_name: input here]",
            "```",
            "",
            "---",
        ]

        # Generate module sections from loaded manifests
        for module in sorted(self._modules.values(), key=lambda m: m.name):
            lines += ["", f"## {module.name}", f"*{module.description}*", ""]

            if module.tools:
                lines += ["| Natural Trigger | Tool Name | Description |", "|---|---|---|"]
                for tool in module.tools:
                    phrases = trigger_map.get(tool.name, [])
                    if phrases:
                        trigger_str = " / ".join(f"`{p}`" for p in phrases)
                    else:
                        trigger_str = f"`[TOOL:{tool.name}: input]`"
                    lines.append(
                        f"| {trigger_str} | `{tool.name}` | {tool.description[:60]} |"
                    )
                lines.append("")

                # Add examples
                examples = [t.example for t in module.tools if t.example]
                if examples:
                    lines.append("```")
                    for ex in examples[:4]:
                        lines.append(ex)
                    lines.append("```")

            lines += ["", "---"]

        # Static sections
        lines += [
            "",
            "## Canvas Push Syntax",
            "*For Ethica or modules to push content to the Living Canvas*",
            "",
            "```",
            "[CANVAS:TabName: content here]",
            "[DEBUG:TabName:lang: code here]",
            "[PROJECT: task one",
            "task two]",
            "[PROJECT:SprintName: task list]",
            "[SKETCH: annotation text]",
            "```",
            "",
            "---",
            "",
            "## Quick Reference Card",
            "",
            "```",
        ]

        # Auto-build quick reference from triggers
        for module in sorted(self._modules.values(), key=lambda m: m.name):
            if module.triggers:
                trigger_str = " / ".join(module.triggers[:4])
                lines.append(f"{trigger_str}")

        lines += [
            "```",
            "",
            "---",
            "",
            "## Dev Note — Adding New Modules",
            "",
            "When adding a new module, triggers must be registered in **three places** in `chat_engine.py`:",
            "",
            "1. **`MODULE_TRIGGERS` dict** — maps trigger phrase → `(tool_name, default_input)`",
            "2. **`is_tool_trigger()` method** — the `_triggers` list that routes to Ops vs chat bubble",
            "3. **`_diff_triggers` tuple** in `_pre_intercept` — **only needed if the tool receives file paths**",
            "",
            "Missing #1 = tool never fires.",
            "Missing #2 = result routes to chat bubble instead of Ops.",
            "Missing #3 (for file-path tools only) = wormbot_scan intercepts the command.",
            "",
            "---",
            f"*Auto-generated {now} — {mod_count} modules, {tool_count} tools*",
            "*Ethica v0.1 — Walks Beside — Free Always — Built by Victory ⟁Σ∿∞*",
        ]

        # Write to file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_path = os.path.join(base_dir, "ETHICA_TOOL_APPENDIX.md")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return (
                f"ModuleRegistry — appendix generated\n"
                f"  {mod_count} modules, {tool_count} tools\n"
                f"  Written to: {out_path}\n"
                f"  Timestamp: {now}"
            )
        except Exception as e:
            return f"ModuleRegistry — appendix write error: {e}"


