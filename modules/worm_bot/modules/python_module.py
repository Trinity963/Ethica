from base_module import BaseModule
from pathlib import Path
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

    def analyze_code(self, code: str, filepath=None) -> dict:
        """Deep Python analysis — AST, pyflakes, style, patterns."""
        issues = []

        # 1. Syntax check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error line {e.lineno}: {e.msg}")
            return {"issues": issues}

        # 2. Alias-aware / scope-aware / lazy-load import analysis
        import_entries = []  # (lineno, local_name, display, is_lazy)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Detect lazy-load: inside a function or try/except
                is_lazy = False
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Try)):
                        for child in ast.walk(parent):
                            if child is node:
                                is_lazy = True
                                break
                    if is_lazy:
                        break
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        local_name = alias.asname if alias.asname else alias.name.split(".")[0]
                        display = f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                        import_entries.append((node.lineno, local_name, display, is_lazy))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        local_name = alias.asname if alias.asname else alias.name
                        mod = node.module or ""
                        display = f"from {mod} import {alias.name}" + (f" as {alias.asname}" if alias.asname else "")
                        import_entries.append((node.lineno, local_name, display, is_lazy))

        # Skip UNUSED check for __init__.py — all relative imports are re-exports
        if filepath is not None and Path(filepath).name == "__init__.py":
            import_entries = []

        # Collect all Name references across entire tree (all scopes)
        used_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        # Also catch attribute access roots: import X; X.something
        used_names |= {n.value.id for n in ast.walk(tree)
                       if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}

        for lineno, local_name, display, is_lazy in import_entries:
            if local_name not in used_names:
                if is_lazy:
                    issues.append(f"Line {lineno}: LAZY_LOAD not used in outer scope — {display}")
                else:
                    issues.append(f"Line {lineno}: UNUSED import — {display}")

        # Pyflakes for non-import issues only (undefined names, redefined, etc.)
        if HAS_PYFLAKES:
            try:
                w = pyflakes_checker.Checker(tree, "<wormbot>")
                for msg in w.messages:
                    text = str(msg).split("<wormbot>:")[-1].strip()
                    # Skip import messages — handled above
                    if ("imported but unused" in text or
                            "redefinition of unused" in text or
                            "unable to detect undefined names" in text):
                        continue
                    issues.append(text)
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
