from base_module import BaseModule
import re

# ============================================================
# WormBot — css_module.py
# CSS analyzer and fixer — upgraded from pattern matching
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

class CSSModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        """Analyze CSS for real issues — units, vendor prefixes, deprecated values."""
        issues = []
        lines  = code.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("/*"):
                continue

            # ── Deprecated / accessibility ────────────────────
            if re.search(r'color\s*:\s*red\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: 'color: red' — use a named variable or accessible hex value.")

            if re.search(r'font-size\s*:\s*\d+px\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Hardcoded px font-size — prefer rem or em for accessibility.")

            if re.search(r'display\s*:\s*-webkit-box\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Old flexbox syntax — use 'display: flex'.")

            # ── Missing vendor prefixes ───────────────────────
            if re.search(r'^\s*transform\s*:', stripped) and \
               not re.search(r'-webkit-transform', code):
                issues.append(f"Line {i}: 'transform' may need '-webkit-transform' for older browsers.")

            if re.search(r'^\s*transition\s*:', stripped) and \
               not re.search(r'-webkit-transition', code):
                issues.append(f"Line {i}: 'transition' may need '-webkit-transition' for older browsers.")

            # ── !important overuse ────────────────────────────
            if "!important" in stripped:
                issues.append(f"Line {i}: '!important' found — consider refactoring specificity instead.")

            # ── Zero units ────────────────────────────────────
            if re.search(r':\s*0(px|em|rem|%)\b', stripped):
                issues.append(f"Line {i}: Use bare '0' instead of '0px/0em/0rem' — units on zero are redundant.")

            # ── Shorthand opportunities ───────────────────────
            if re.search(r'margin-(top|right|bottom|left)\s*:', stripped):
                issues.append(f"Line {i}: Individual margin property — consider margin shorthand.")

            if re.search(r'padding-(top|right|bottom|left)\s*:', stripped):
                issues.append(f"Line {i}: Individual padding property — consider padding shorthand.")

            # ── Duplicate selectors (basic) ───────────────────
            selectors = re.findall(r'^([^{]+)\s*\{', stripped)
            seen = set()
            for sel in selectors:
                sel = sel.strip()
                if sel in seen:
                    issues.append(f"Line {i}: Duplicate selector '{sel}' — merge rules.")
                seen.add(sel)

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Apply safe automatic CSS fixes."""
        fixed = code

        # color: red → accessible default
        fixed = re.sub(
            r'color\s*:\s*red\s*;',
            'color: #cc0000;',
            fixed, flags=re.IGNORECASE
        )

        # font-size: Npx → rem equivalent (16px base)
        def px_to_rem(m):
            px_val = int(re.search(r'(\d+)px', m.group(0)).group(1))
            rem_val = round(px_val / 16, 4)
            return f'font-size: {rem_val}rem;'
        fixed = re.sub(r'font-size\s*:\s*\d+px\s*;', px_to_rem, fixed, flags=re.IGNORECASE)

        # 0px / 0em / 0rem / 0% → 0
        fixed = re.sub(r'\b0(px|em|rem|%)\b', '0', fixed)

        # Old flexbox
        fixed = re.sub(
            r'display\s*:\s*-webkit-box\s*;',
            'display: flex;',
            fixed, flags=re.IGNORECASE
        )

        return fixed
