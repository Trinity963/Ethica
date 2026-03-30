from base_module import BaseModule
import re

# ============================================================
# WormBot — html_module.py
# HTML analyzer and fixer — upgraded from pattern matching
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

class HTMLModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        """Analyze HTML for real issues — semantics, accessibility, deprecated tags."""
        issues = []
        lines  = code.splitlines()

        # ── Doctype ───────────────────────────────────────────
        if not re.search(r'<!DOCTYPE\s+html', code, re.IGNORECASE):
            issues.append("Missing <!DOCTYPE html> declaration.")

        # ── Per-line checks ───────────────────────────────────
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            # Deprecated tags
            if re.search(r'<center\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Deprecated <center> — use CSS text-align instead.")

            if re.search(r'<font\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Deprecated <font> — use CSS for typography.")

            if re.search(r'<b\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: <b> is presentational — use <strong> for semantic emphasis.")

            if re.search(r'<i\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: <i> is presentational — use <em> for semantic emphasis.")

            if re.search(r'<marquee\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Deprecated <marquee> — use CSS animations.")

            if re.search(r'<blink\b', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Deprecated <blink> — removed from all modern browsers.")

            # Accessibility — images without alt
            img_tags = re.findall(r'<img\b[^>]*>', stripped, re.IGNORECASE)
            for tag in img_tags:
                if 'alt=' not in tag.lower():
                    issues.append(f"Line {i}: <img> missing alt attribute — required for accessibility.")

            # Inline styles
            if re.search(r'\bstyle\s*=\s*["\']', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Inline style found — move to external CSS.")

            # Inline event handlers
            if re.search(r'\bon\w+\s*=\s*["\']', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Inline event handler — use addEventListener in JS instead.")

            # Empty tags
            if re.search(r'<(div|span|p|section|article)\s*>\s*</', stripped, re.IGNORECASE):
                issues.append(f"Line {i}: Empty element found — remove or populate.")

            # Non-semantic layout divs (basic heuristic)
            if re.search(r'<div\s+class=["\']?(header|footer|nav|main|sidebar)', stripped, re.IGNORECASE):
                tag = re.search(r'(header|footer|nav|main|aside)', stripped, re.IGNORECASE)
                if tag:
                    issues.append(f"Line {i}: <div class='{tag.group(0)}'> — use semantic <{tag.group(0)}> instead.")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Apply safe automatic HTML fixes."""
        fixed = code

        # Add doctype if missing
        if not re.search(r'<!DOCTYPE\s+html', fixed, re.IGNORECASE):
            fixed = "<!DOCTYPE html>\n" + fixed

        # Deprecated tags → semantic/CSS equivalents
        fixed = re.sub(
            r'<center>',
            "<div style='text-align:center;'>",
            fixed, flags=re.IGNORECASE
        )
        fixed = re.sub(r'</center>', '</div>', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'<font[^>]*>', '', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'</font>', '', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'<marquee[^>]*>', '<div>', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'</marquee>', '</div>', fixed, flags=re.IGNORECASE)

        # <b> → <strong>, <i> → <em>
        fixed = re.sub(r'<b\b([^>]*)>', r'<strong\1>', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'</b>', '</strong>', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'<i\b([^>]*)>', r'<em\1>', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'</i>', '</em>', fixed, flags=re.IGNORECASE)

        # Add alt="" to img tags missing alt
        def add_alt(m):
            tag = m.group(0)
            if 'alt=' not in tag.lower():
                tag = tag[:-1] + ' alt="">'
            return tag
        fixed = re.sub(r'<img\b[^>]*>', add_alt, fixed, flags=re.IGNORECASE)

        return fixed
