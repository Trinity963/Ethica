from base_module import BaseModule
import re

# ============================================================
# WormBot — markdown_module.py
# Markdown analyzer and fixer — syntax error fixed, upgraded
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

class MarkdownModule(BaseModule):

    def analyze_code(self, code: str) -> dict:
        """Analyze Markdown for structure, formatting, and link issues."""
        issues = []
        lines  = code.splitlines()

        # ── Document structure ────────────────────────────────
        if not any(line.startswith("# ") for line in lines):
            issues.append("No top-level heading (H1) found — add a '# Title' at the top.")

        # ── Per-line checks ───────────────────────────────────
        in_code_block = False
        h_levels = []

        for i, line in enumerate(lines, 1):

            # Track fenced code blocks — skip content inside
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Heading hierarchy
            h_match = re.match(r'^(#{1,6})\s', line)
            if h_match:
                level = len(h_match.group(1))
                if h_levels and level > h_levels[-1] + 1:
                    issues.append(f"Line {i}: Heading level jumps from H{h_levels[-1]} to H{level} — skipped level.")
                h_levels.append(level)

            # Trailing whitespace
            if line != line.rstrip():
                issues.append(f"Line {i}: Trailing whitespace found.")

            # Bare URLs — should be formatted as links
            bare_url = re.search(r'(?<!\()(https?://[^\s\)]+)(?!\))', line)
            if bare_url and not re.search(r'\[.*?\]\(', line):
                issues.append(f"Line {i}: Bare URL found — wrap as [text](url) for clarity.")

            # Broken link syntax — text but no URL
            broken_link = re.search(r'\[([^\]]+)\]\(\s*\)', line)
            if broken_link:
                issues.append(f"Line {i}: Empty link URL for '{broken_link.group(1)}'.")

            # Multiple blank lines
            if i > 1 and line.strip() == "" and lines[i-2].strip() == "":
                issues.append(f"Line {i}: Multiple consecutive blank lines — use single blank line.")

            # Hard tabs
            if "\t" in line:
                issues.append(f"Line {i}: Hard tab found — use spaces for consistent rendering.")

            # Long lines in prose (not headings or code)
            if len(line) > 120 and not line.startswith("#"):
                issues.append(f"Line {i}: Line exceeds 120 characters — consider wrapping.")

        return {"issues": issues}

    def fix_code(self, code: str) -> str:
        """Apply safe automatic Markdown fixes."""
        fixed = code
        lines = fixed.splitlines()
        result = []
        in_code_block = False
        prev_blank = False

        for line in lines:
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                result.append(line)
                prev_blank = False
                continue

            if in_code_block:
                result.append(line)
                continue

            # Remove trailing whitespace
            line = line.rstrip()

            # Collapse multiple blank lines into one
            if line == "":
                if prev_blank:
                    continue
                prev_blank = True
            else:
                prev_blank = False

            # Convert hard tabs to 4 spaces
            line = line.replace("\t", "    ")

            result.append(line)

        fixed = "\n".join(result)

        # Add H1 if missing
        if not any(l.startswith("# ") for l in fixed.splitlines()):
            fixed = "# Document\n\n" + fixed

        return fixed
