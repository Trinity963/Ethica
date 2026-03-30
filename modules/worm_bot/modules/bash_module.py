from base_module import BaseModule
import re

# ============================================================
# WormBot — bash_module.py
# Bash analyzer and fixer
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

class BashModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        issues = []
        lines  = code.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if re.search(r'\[\s*.*==.*\]', stripped):
                issues.append(f"Line {i}: Use '=' not '==' for string comparison in [ ].")
            unquoted = re.findall(r'(?<!\[)\$(\w+)(?!\w*["\'])', stripped)
            for var in unquoted:
                if var not in ('0','1','2','?','#','@','*','$','!'):
                    issues.append(f"Line {i}: Unquoted variable '${var}' — use \"${{{var}}}\".")
                    break
            if re.search(r'\bif\b.*\bthen\b', stripped):
                issues.append(f"Line {i}: 'if' and 'then' on same line — separate with newline or semicolon.")
            if re.search(r'^\s*cd\s+', stripped):
                next_line = lines[i].strip() if i < len(lines) else ''
                if not re.search(r'\$\?|pipefail|errexit|-e\b', next_line):
                    issues.append(f"Line {i}: 'cd' without error check — consider 'cd /path || exit 1'.")
            if '`' in stripped:
                issues.append(f"Line {i}: Backtick substitution — use $(...) instead.")
            if re.search(r'\becho\s+[^"\']', stripped):
                issues.append(f"Line {i}: 'echo' with unquoted string — quote for safety.")

        if lines and not lines[0].startswith('#!'):
            issues.append("Missing shebang line — add '#!/bin/bash' at top.")
        if_count = sum(1 for l in lines if re.match(r'\s*if\b', l))
        fi_count = sum(1 for l in lines if re.match(r'\s*fi\b', l))
        if if_count != fi_count:
            issues.append(f"Unmatched if/fi — {if_count} 'if' but {fi_count} 'fi'.")
        for_count  = sum(1 for l in lines if re.match(r'\s*for\b', l))
        done_count = sum(1 for l in lines if re.match(r'\s*done\b', l))
        if for_count != done_count:
            issues.append(f"Unmatched for/done — {for_count} 'for' but {done_count} 'done'.")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        fixed = code
        lines = fixed.splitlines()
        result = []
        if lines and not lines[0].startswith('#!'):
            result.append('#!/bin/bash')
        for line in lines:
            line = re.sub(
                r'(\[(?:[^\]]*?))\s*==\s*([^\]]*?\])',
                lambda m: m.group(0).replace('==', '='),
                line
            )
            line = re.sub(r'`([^`]+)`', r'$(\1)', line)
            result.append(line)
        return '\n'.join(result)
