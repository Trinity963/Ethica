# ============================================================
# Ethica v0.1 — autonomous_debugger.py
# Ethica's Autonomous Debug Loop
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Ethica runs the code. Reads the error. Rewrites the fix.
# Pushes it back. Runs again. Up to 3 attempts.
# After each attempt she knows what changed and why.
# At the end — clean or not — she reports back to V.
#
# V watches. V approves. This is co-creation at the execution layer.
# ============================================================

import subprocess
import sys
import os
import re
import tempfile
import threading
from datetime import datetime


MAX_ATTEMPTS = 3
TIMEOUT      = 30  # seconds per run


class DebugAttempt:
    """One iteration of the autonomous debug loop."""
    def __init__(self, attempt_number, code, stdout, stderr, returncode, duration):
        self.attempt_number = attempt_number
        self.code           = code
        self.stdout         = stdout
        self.stderr         = stderr
        self.returncode     = returncode
        self.duration       = duration
        self.success        = returncode == 0 and not stderr.strip()

    def error_summary(self):
        if not self.stderr:
            return None
        lines = self.stderr.strip().splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("File") and not line.startswith("Traceback"):
                return line
        return lines[-1] if lines else None

    def error_line(self):
        matches = re.findall(r'line (\d+)', self.stderr or "")
        return int(matches[-1]) if matches else None


class AutonomousDebugger:
    """
    Ethica's autonomous debug loop.

    Given code, she runs it, reads the error, rewrites the fix,
    and iterates up to MAX_ATTEMPTS times.

    Runs entirely in a background thread — UI stays responsive.
    Reports progress and final result via callbacks.
    """

    def __init__(self, connector, config):
        self.connector = connector
        self.config    = config

    def run(self, code, lang="Python", on_attempt=None, on_complete=None):
        """
        Start the autonomous debug loop in a background thread.

        on_attempt(attempt: DebugAttempt, message: str)
            — called after each run with Ethica's commentary
        on_complete(attempts: list, final_code: str, success: bool, summary: str)
            — called when loop ends (success or max attempts)
        """
        thread = threading.Thread(
            target=self._loop,
            args=(code, lang, on_attempt, on_complete),
            daemon=True,
            name="EthicaAutonomousDebug"
        )
        thread.start()

    # ── Core Loop ─────────────────────────────────────────────

    def _loop(self, code, lang, on_attempt, on_complete):
        attempts  = []
        current_code = code
        runner = self._get_runner(lang)
        ext    = self._get_ext(lang)

        for i in range(1, MAX_ATTEMPTS + 1):
            print(f"[AutonomousDebug] Attempt {i}/{MAX_ATTEMPTS}")

            # Run the code
            attempt = self._execute(current_code, runner, ext, i)
            attempts.append(attempt)

            # Generate Ethica's commentary for this attempt
            message = self._commentary(attempt, i, len(attempts))

            if on_attempt:
                on_attempt(attempt, message)

            if attempt.success:
                # Clean — report success
                summary = self._success_summary(attempts, current_code)
                if on_complete:
                    on_complete(attempts, current_code, True, summary)
                return

            if i < MAX_ATTEMPTS:
                # Rewrite the code for next attempt
                fixed_code = self._rewrite(current_code, attempt)
                if fixed_code and fixed_code.strip() != current_code.strip():
                    current_code = fixed_code
                else:
                    # Model couldn't improve it — stop early
                    summary = self._failure_summary(attempts, current_code)
                    if on_complete:
                        on_complete(attempts, current_code, False, summary)
                    return

        # Hit max attempts without success
        summary = self._failure_summary(attempts, current_code)
        if on_complete:
            on_complete(attempts, current_code, False, summary)

    # ── Execution ─────────────────────────────────────────────

    def _execute(self, code, runner, ext, attempt_number):
        start = datetime.now()
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=ext,
                delete=False,
                encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                [runner, tmp_path],
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                encoding="utf-8"
            )
            duration = (datetime.now() - start).total_seconds()
            return DebugAttempt(
                attempt_number = attempt_number,
                code           = code,
                stdout         = result.stdout,
                stderr         = result.stderr,
                returncode     = result.returncode,
                duration       = duration
            )
        except subprocess.TimeoutExpired:
            return DebugAttempt(
                attempt_number = attempt_number,
                code           = code,
                stdout         = "",
                stderr         = f"Timed out after {TIMEOUT}s",
                returncode     = -1,
                duration       = TIMEOUT
            )
        except Exception as e:
            return DebugAttempt(
                attempt_number = attempt_number,
                code           = code,
                stdout         = "",
                stderr         = str(e),
                returncode     = -1,
                duration       = 0
            )
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    # ── Rewrite ───────────────────────────────────────────────

    def _rewrite(self, code, attempt):
        """Ask the model to fix the code based on the error."""
        error   = attempt.stderr or "Unknown error"
        summary = attempt.error_summary() or error
        line    = attempt.error_line()
        line_ref = f" on line {line}" if line else ""

        prompt = f"""Fix this code. It failed{line_ref} with this error:

{error.strip()}

Original code:
```
{code.strip()}
```

Return ONLY the corrected code — no explanation, no markdown fences, no preamble.
Just the raw fixed code ready to run."""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Ethica — a co-creator and code debugger. "
                    "You fix code precisely. You return ONLY raw runnable code. "
                    "No markdown. No explanation. No fences. Just the code."
                )
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = ""
            for token in self.connector.chat(messages, stream=True):
                response += token

            # Strip think blocks
            response = re.sub(r'<think>[\s\S]*?</think>', '', response).strip()

            # Strip any accidental markdown fences
            response = re.sub(r'^```[\w]*\n?', '', response, flags=re.MULTILINE)
            response = re.sub(r'\n?```$', '', response, flags=re.MULTILINE)

            return response.strip() if response.strip() else None

        except Exception as e:
            print(f"[AutonomousDebug] Rewrite error: {e}")
            return None

    # ── Commentary ────────────────────────────────────────────

    def _commentary(self, attempt, attempt_num, total_so_far):
        """Brief Ethica commentary on a single attempt."""
        if attempt.success:
            if attempt_num == 1:
                return f"Ran clean first try. Done."
            else:
                return f"Fixed it on attempt {attempt_num}. Clean."

        error   = attempt.error_summary() or "unknown error"
        line    = attempt.error_line()
        line_ref = f" on line {line}" if line else ""

        if attempt_num < MAX_ATTEMPTS:
            return f"Attempt {attempt_num} failed{line_ref} — {error}. Rewriting."
        else:
            return f"Attempt {attempt_num} — still failing{line_ref}. {error}. Handing back to you."

    # ── Summaries ─────────────────────────────────────────────

    def _success_summary(self, attempts, final_code):
        n = len(attempts)
        if n == 1:
            return "Ran clean on the first attempt."
        else:
            errors = [a.error_summary() for a in attempts[:-1] if a.error_summary()]
            error_list = ", ".join(f'"{e}"' for e in errors) if errors else "the errors"
            return (
                f"Fixed in {n} attempts. "
                f"Worked through {error_list}. "
                f"Final code is on the debug tab."
            )

    def _failure_summary(self, attempts, final_code):
        last = attempts[-1]
        error = last.error_summary() or "unknown error"
        line  = last.error_line()
        line_ref = f" around line {line}" if line else ""
        return (
            f"Hit {MAX_ATTEMPTS} attempts without a clean run. "
            f"Last error{line_ref}: {error}. "
            f"Best version is on the debug tab — take a look."
        )

    # ── Helpers ───────────────────────────────────────────────

    def _get_runner(self, lang):
        runners = {
            "Python": sys.executable,
            "Bash":   "/bin/bash"
        }
        return runners.get(lang, sys.executable)

    def _get_ext(self, lang):
        exts = {
            "Python": ".py",
            "Bash":   ".sh"
        }
        return exts.get(lang, ".py")
