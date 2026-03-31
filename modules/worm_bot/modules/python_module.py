from base_module import BaseModule
import ast
import re

try:
    import pyflakes.checker as pyflakes_checker
    HAS_PYFLAKES = True
except ImportError:
    HAS_PYFLAKES = False

try:
    import autopep8
    HAS_AUTOPEP8 = True
except ImportError:
    HAS_AUTOPEP8 = False


class PythonModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        """Deep Python analysis — AST, pyflakes, style, patterns."""
        issues = []

        # 1. Syntax check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error line {e.lineno}: {e.msg}")
            return {"issues": issues}

        # 2. Pyflakes — unused imports, undefined names
        if HAS_PYFLAKES:
            try:
                w = pyflakes_checker.Checker(tree, "<wormbot>")
                for msg in w.messages:
                    issues.append(str(msg).split("<wormbot>:")[-1].strip())
            except Exception:
                pass

        # 3. Duplicate imports
        seen_imports = []
        for line in code.splitlines():
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                if s in seen_imports:
                    issues.append(f"Duplicate import: {s}")
                seen_imports.append(s)

        # 4. Print statements
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                issues.append(f"Line {i}: print() found — consider logging")

        # 5. Bare except
        for i, line in enumerate(code.splitlines(), 1):
            if re.match(r"\s*except\s*:", line):
                issues.append(f"Line {i}: bare except — catch specific exceptions")

        # 6. Mutable default arguments
        for i, line in enumerate(code.splitlines(), 1):
            if re.search(r"def\s+\w+\s*\(.*=\s*[\[{]", line):
                issues.append(f"Line {i}: possible mutable default argument")

        # 7. Deep nesting
        max_indent = max(
            (len(l) - len(l.lstrip()) for l in code.splitlines() if l.strip()),
            default=0
        )
        if max_indent > 20:
            issues.append(f"Deep nesting detected (max indent: {max_indent}) — consider refactoring")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Fix Python — autopep8 + targeted fixes."""
        fixed = code

        # 1. autopep8
        if HAS_AUTOPEP8:
            try:
                fixed = autopep8.fix_code(fixed, options={"aggressive": 1, "max_line_length": 120})
            except Exception:
                pass

        # 2. Remove duplicate imports
        lines = fixed.splitlines(keepends=True)
        seen = set()
        deduped = []
        for line in lines:
            s = line.strip()
            if s.startswith("import ") or s.startswith("from "):
                if s in seen:
                    continue
                seen.add(s)
            deduped.append(line)
        fixed = "".join(deduped)

        # 3. Replace print with logging
        if re.search(r"\bprint\s*\(", fixed):
            has_logging = "import logging" in fixed
            fixed = re.sub(r"\bprint\s*\(", "logging.info(", fixed)
            if not has_logging:
                fixed = "import logging\n" + fixed

        # 4. Bare except → except Exception
        fixed = re.sub(r"(\s*)except\s*:\s*\n", r"\1except Exception:\n", fixed)

        return fixed
