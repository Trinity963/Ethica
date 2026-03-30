# ============================================================
# Ethica v0.1 — tool_registry.py
# Orchestration Kernel — Tool Registry
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Ethica is not a chatbot. She is a conductor.
# This registry is her instrument drawer.
# Every tool here is available for her to reach for.
#
# Tools are registered with:
#   - name       : what Ethica calls it
#   - description: what it does in plain language
#   - handler    : the Python function that executes it
#
# Ethica invokes tools via response syntax:
#   [TOOL:tool_name: input]
#
# The kernel intercepts, executes, injects result,
# and Ethica responds naturally with the output.
# ============================================================

import json
import os
import subprocess
import datetime
import math


# ── Tool Registry ─────────────────────────────────────────────

class ToolRegistry:
    """
    The Orchestration Kernel tool registry.
    Manages all tools Ethica can reach for.
    Tools are callable, sandboxed, and result-aware.
    """

    def __init__(self):
        self._tools = {}
        self._register_builtin_tools()

    # ── Registration ──────────────────────────────────────────

    def register(self, name, description, handler, category="general"):
        """
        Register a tool.
        name        : identifier Ethica uses  eg "web_search"
        description : what it does            eg "Search the web for current information"
        handler     : callable(input) -> str  eg search_fn
        category    : grouping for UI         eg "web", "system", "math"
        """
        self._tools[name.lower()] = {
            "name":        name.lower(),
            "description": description,
            "handler":     handler,
            "category":    category,
            "enabled":     True,
        }

    def enable(self, name):
        if name in self._tools:
            self._tools[name]["enabled"] = True

    def disable(self, name):
        if name in self._tools:
            self._tools[name]["enabled"] = False

    # ── Usage Tracking ───────────────────────────────────────

    def _increment_usage(self, name):
        """Increment tool usage counter in river_state.json."""
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

    def _check_integrity_async(self):
        """Run integrity check in background after tool execution. Warns via Ops on mismatch."""
        import threading
        def _run():
            try:
                from modules.ethica_guard.ethica_guard import startup_check
                warning = startup_check()
                if warning:
                    import json, os, datetime
                    # Log to memory/crashes/
                    crash_dir = os.path.expanduser("~/Ethica/memory/crashes")
                    os.makedirs(crash_dir, exist_ok=True)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    log = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "trigger": "tool_write",
                        "warning": warning
                    }
                    with open(os.path.join(crash_dir, f"integrity_{ts}.json"), "w") as f:
                        json.dump(log, f, indent=2)
                    # Write warning to status file — main_window drains it
                    try:
                        import os
                        status_path = os.path.expanduser("~/Ethica/status/integrity_warning.json")
                        with open(status_path, "w") as sf:
                            json.dump({"warning": warning, "timestamp": datetime.datetime.now().isoformat()}, sf, indent=2)
                    except Exception:
                        pass
            except Exception:
                pass  # never break tool execution over integrity check
        threading.Thread(target=_run, daemon=True).start()

    # ── Execution ─────────────────────────────────────────────────

    def execute(self, name, input_text):
        """
        Execute a tool by name with given input.
        Returns (success, result_string)
        """
        name = name.lower().strip()

        if name not in self._tools:
            return False, f"Unknown tool: {name}"

        tool = self._tools[name]

        if not tool["enabled"]:
            return False, f"Tool '{name}' is currently disabled"

        try:
            result = tool["handler"](input_text.strip())
            self._increment_usage(name)
            self._check_integrity_async()
            return True, str(result)
        except Exception as e:
            return False, f"Tool '{name}' failed: {str(e)}"

    # ── Introspection ─────────────────────────────────────────

    def list_tools(self):
        """Return list of all registered tools."""
        return [
            {
                "name":        t["name"],
                "description": t["description"],
                "category":    t["category"],
                "enabled":     t["enabled"],
            }
            for t in self._tools.values()
        ]

    def get_system_prompt_block(self):
        """
        Generate the tool section of Ethica's system prompt.
        Tells her what tools exist and exactly how to invoke them.
        """
        enabled = [t for t in self._tools.values() if t["enabled"]]
        if not enabled:
            return ""

        lines = [
            "",
            "--- ORCHESTRATION KERNEL ---",
            "You have access to tools. When you need one, place ONLY this on its own line:",
            "",
            "  [TOOL:tool_name: input]",
            "",
            "CRITICAL RULES:",
            "- The [TOOL:...] block is intercepted automatically — the user NEVER sees it",
            "- NEVER write [TOOL:...] inside a sentence or explanation",
            "- NEVER say 'I will use [TOOL:datetime: now]' — just write the block alone",
            "- After execution you receive the result and respond naturally with it",
            "- Do NOT show the tool syntax in your response — it is invisible infrastructure",
            "",
            "CORRECT — user asks for time, you write ONLY:",
            "  [TOOL:datetime: now]",
            "",
            "WRONG — never do this:",
            "  'Here is the time: [TOOL:datetime: now]'",
            "  'I will check using [TOOL:datetime: now]'",
            "",
            "AVAILABLE TOOLS:",
        ]

        for t in enabled:
            lines.append(f"  {t['name']} — {t['description']}")

        lines += [
            "",
            "EXAMPLES:",
            "  [TOOL:calculate: 2456 * 3.14159]",
            "  [TOOL:datetime: now]",
            "  [TOOL:run_code: print('hello world')]",
            "  [TOOL:read_file: /home/trinity/notes.txt]",
            "",
            "Only invoke tools when genuinely needed.",
            "--- END KERNEL ---",
            "",
        ]

        return "\n".join(lines)

    def has_tool(self, name):
        return name.lower() in self._tools

    # ── Built-in Tools ────────────────────────────────────────

    def _register_builtin_tools(self):
        """Register Ethica's core built-in tools."""

        # ── DateTime ──────────────────────────────────────────
        self.register(
            name="datetime",
            description="Get current date, time, or both. Input: 'now', 'date', 'time', or timezone name.",
            handler=self._tool_datetime,
            category="system"
        )

        # ── Calculator ────────────────────────────────────────
        self.register(
            name="calculate",
            description="Evaluate a mathematical expression precisely. Input: any math expression.",
            handler=self._tool_calculate,
            category="math"
        )

        # ── Run Code ──────────────────────────────────────────
        self.register(
            name="run_code",
            description="Execute Python code and return the output. Input: Python code to run.",
            handler=self._tool_run_code,
            category="code"
        )

        # ── Read File ─────────────────────────────────────────
        self.register(
            name="read_file",
            description="Read a file from the local filesystem. Input: absolute file path.",
            handler=self._tool_read_file,
            category="system"
        )

        # ── Word Count ────────────────────────────────────────
        self.register(
            name="word_count",
            description="Count words, characters, and lines in text. Input: the text to analyze.",
            handler=self._tool_word_count,
            category="text"
        )

        # ── System Info ───────────────────────────────────────
        self.register(
            name="system_info",
            description="Get system information — OS, Python version, available memory. Input: 'all', 'os', 'python', or 'memory'.",
            handler=self._tool_system_info,
            category="system"
        )

    # ── Tool Handlers ─────────────────────────────────────────

    def _tool_datetime(self, input_text):
        now = datetime.datetime.now()
        inp = input_text.lower().strip()

        if inp == "date":
            return now.strftime("%A, %B %d %Y")
        elif inp == "time":
            return now.strftime("%H:%M:%S")
        else:
            return now.strftime("%A, %B %d %Y  —  %H:%M:%S")

    def _tool_calculate(self, expression):
        # Safe math eval — only math operations, no builtins abuse
        safe_globals = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "int": int, "float": float,
            "pi": math.pi, "e": math.e,
            "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "ceil": math.ceil, "floor": math.floor,
        }
        result = eval(expression, safe_globals, {})
        # Format cleanly
        if isinstance(result, float) and result == int(result):
            return str(int(result))
        return str(result)

    def _tool_run_code(self, code):
        # Run in subprocess — sandboxed, timeout 10s
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout.strip()
            error = result.stderr.strip()

            if error and not output:
                return f"Error:\n{error}"
            if error:
                return f"{output}\n\nWarnings:\n{error}"
            return output if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Code execution timed out (10s limit)"

    def _tool_read_file(self, path):
        path = path.strip().strip('"').strip("'")
        if not os.path.exists(path):
            return f"File not found: {path}"
        if os.path.getsize(path) > 100_000:
            return f"File too large to read (>100KB): {path}"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = content.split("\n")
            preview = "\n".join(lines[:100])
            if len(lines) > 100:
                preview += f"\n\n... ({len(lines) - 100} more lines)"
            return preview
        except Exception as e:
            return f"Could not read file: {e}"

    def _tool_word_count(self, text):
        words = len(text.split())
        chars = len(text)
        chars_no_spaces = len(text.replace(" ", ""))
        lines = len(text.split("\n"))
        return (
            f"Words: {words}\n"
            f"Characters: {chars}\n"
            f"Characters (no spaces): {chars_no_spaces}\n"
            f"Lines: {lines}"
        )

    def _tool_system_info(self, query):
        import platform
        import sys
        query = query.lower().strip()

        if query == "os":
            return f"{platform.system()} {platform.release()} ({platform.machine()})"
        elif query == "python":
            return f"Python {sys.version}"
        elif query == "memory":
            try:
                import psutil
                mem = psutil.virtual_memory()
                return (
                    f"Total: {mem.total // (1024**3)}GB\n"
                    f"Available: {mem.available // (1024**3)}GB\n"
                    f"Used: {mem.percent}%"
                )
            except ImportError:
                return "psutil not installed — install for memory info"
        else:
            return (
                f"OS: {platform.system()} {platform.release()}\n"
                f"Python: {sys.version.split()[0]}\n"
                f"Machine: {platform.machine()}"
            )
