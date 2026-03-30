from base_module import BaseModule
import re
import subprocess
import shutil

HAS_NODE = shutil.which("node") is not None

class JSModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        """Deep JS analysis — syntax, patterns, style."""
        issues = []

        # 1. Syntax check via node --check if available
        if HAS_NODE:
            try:
                result = subprocess.run(
                    ["node", "--check", "--input-type=module"],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    for line in result.stderr.splitlines():
                        if line.strip():
                            issues.append(f"Syntax: {line.strip()}")
                    return {"issues": issues}
            except Exception:
                pass

        # 2. var usage — line level
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"\bvar\s+", line) and not line.strip().startswith("//"):
                issues.append(f"Line {i}: var used — prefer let or const")

        # 3. == without === (skip !=, !==, ===, ===>)
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"(?<![=!<>])={2}(?!=)", line) and not line.strip().startswith("//"):
                issues.append(f"Line {i}: == found — use === for strict equality")

        # 4. alert/confirm/prompt
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"\b(alert|confirm|prompt)\s*\(", line) and not line.strip().startswith("//"):
                issues.append(f"Line {i}: {re.search(r'(alert|confirm|prompt)', line).group()} — replace with custom dialog")

        # 5. console.log in production code
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"\bconsole\.log\s*\(", line) and not line.strip().startswith("//"):
                issues.append(f"Line {i}: console.log found — remove for production")

        # 6. Missing semicolons on statement lines
        missing_semi = 0
        for line in code.splitlines():
            s = line.strip()
            if (s and
                not s.startswith("//") and
                not s.startswith("*") and
                not s.startswith("/*") and
                not s.endswith("{") and
                not s.endswith("}") and
                not s.endswith(",") and
                not s.endswith(";") and
                not s.endswith("(") and
                re.search(r"(let|const|var|return|throw)\s+", s)):
                missing_semi += 1
        if missing_semi > 0:
            issues.append(f"{missing_semi} line(s) may be missing semicolons")

        # 7. == null instead of === null
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"==\s*null", line) and "===" not in line:
                issues.append(f"Line {i}: use === null for null checks")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Fix JS — safe targeted replacements."""
        lines = code.splitlines()
        result = []

        for line in lines:
            stripped = line.strip()
            indent   = len(line) - len(line.lstrip())
            pad      = " " * indent

            # Skip already commented lines
            if stripped.startswith("//"):
                result.append(line)
                continue

            # 1. var → let
            line = re.sub(r"\bvar\b", "let", line)

            # 2. == → === (safe — skip !==, ===)
            line = re.sub(r"(?<![=!<>])={2}(?!=)", "===", line)

            # 3. alert → TODO comment above + keep line
            if re.search(r"\balert\s*\(", line):
                cur_indent = len(line) - len(line.lstrip())
                cur_pad    = " " * cur_indent
                result.append(f"{cur_pad}// TODO: replace alert with custom dialog")
                result.append(line)
                continue

            # 4. console.log → comment out
            if re.search(r"\bconsole\.log\s*\(", line):
                result.append(f"{pad}// {stripped}")
                continue

            result.append(line)

        return "\n".join(result)
