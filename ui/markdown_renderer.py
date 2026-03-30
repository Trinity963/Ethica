# ============================================================
# Ethica v0.1 — markdown_renderer.py
# Lightweight Markdown → Tkinter Widget Renderer
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Renders Ethica's markdown responses as styled widgets.
# No external libraries — pure Tkinter.
#
# Supports:
#   # ## ###     headings
#   **bold**     bold inline
#   `code`       inline code
#   - item       bullet list
#   1. item      numbered list
#   plain text   normal paragraph
#   blank line   paragraph spacing
# ============================================================

import tkinter as tk
import re


class MarkdownRenderer:
    """
    Renders markdown text into a Tkinter frame as styled widgets.

    Usage:
        renderer = MarkdownRenderer(parent_frame, theme, wraplength=520)
        renderer.render("**Hello** world\n\n- item one\n- item two")
    """

    def __init__(self, parent, theme, wraplength=520, bg=None):
        self.parent = parent
        self.theme = theme
        self.wraplength = wraplength
        self._bg = bg  # override background if needed

    # ── Public API ────────────────────────────────────────────

    def render(self, text):
        """
        Parse and render markdown text into parent frame.
        Creates Tkinter widgets for each block.
        """
        c = self.theme.colors
        bg = self._bg or c["bubble_ethica"]

        blocks = self._parse_blocks(text)

        for block in blocks:
            self._render_block(block, bg)

    # ── Block Parser ──────────────────────────────────────────

    def _parse_blocks(self, text):
        """
        Split text into semantic blocks.
        Returns list of (type, content) tuples.
        """
        blocks = []
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines — add spacing
            if not stripped:
                blocks.append(("spacer", ""))
                i += 1
                continue

            # Heading 1
            if stripped.startswith("# "):
                blocks.append(("h1", stripped[2:].strip()))
                i += 1
                continue

            # Heading 2
            if stripped.startswith("## "):
                blocks.append(("h2", stripped[3:].strip()))
                i += 1
                continue

            # Heading 3
            if stripped.startswith("### "):
                blocks.append(("h3", stripped[4:].strip()))
                i += 1
                continue

            # Unordered list item
            if stripped.startswith("- ") or stripped.startswith("* "):
                blocks.append(("bullet", stripped[2:].strip()))
                i += 1
                continue

            # Numbered list item
            num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
            if num_match:
                blocks.append((
                    "numbered",
                    (num_match.group(1), num_match.group(2).strip())
                ))
                i += 1
                continue

            # Code block (triple backtick)
            if stripped.startswith("```"):
                code_lines = []
                i += 1
                while i < len(lines):
                    if lines[i].strip().startswith("```"):
                        i += 1
                        break
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(("code_block", "\n".join(code_lines)))
                continue

            # Regular paragraph
            blocks.append(("paragraph", stripped))
            i += 1

        return blocks

    # ── Block Renderer ────────────────────────────────────────

    def _render_block(self, block, bg):
        """Render a single block as a Tkinter widget."""
        btype, content = block
        c = self.theme.colors
        f = self.theme.font

        if btype == "spacer":
            tk.Frame(
                self.parent,
                bg=bg,
                height=4
            ).pack(fill=tk.X)

        elif btype == "h1":
            self._render_inline(
                content, bg,
                font=f("title"),
                fg=c["accent_bright"],
                pady=(6, 2)
            )

        elif btype == "h2":
            self._render_inline(
                content, bg,
                font=f("heading"),
                fg=c["accent_bright"],
                pady=(4, 2)
            )

        elif btype == "h3":
            self._render_inline(
                content, bg,
                font=f("body_bold"),
                fg=c["accent_bright"],
                pady=(3, 1)
            )

        elif btype == "bullet":
            self._render_bullet(content, bg, prefix="•")

        elif btype == "numbered":
            number, text = content
            self._render_bullet(text, bg, prefix=f"{number}.")

        elif btype == "code_block":
            self._render_code_block(content, bg)

        elif btype == "paragraph":
            self._render_paragraph(content, bg)

    # ── Inline Renderers ──────────────────────────────────────

    def _render_paragraph(self, text, bg):
        """
        Render a paragraph with inline markdown support.
        Handles **bold** and `code` inline.
        """
        c = self.theme.colors
        f = self.theme.font

        # Check if paragraph has any inline markup
        has_markup = "**" in text or "`" in text

        if not has_markup:
            # Plain text — fast path
            tk.Label(
                self.parent,
                text=text,
                bg=bg,
                fg=c["text_ethica"],
                font=f("body"),
                wraplength=self.wraplength,
                justify=tk.LEFT,
                anchor=tk.W,
                pady=1
            ).pack(fill=tk.X, anchor=tk.W)
            return

        # Has inline markup — render as Text widget with tags
        self._render_inline_rich(text, bg)

    def _render_inline(self, text, bg, font, fg, pady=(1, 1)):
        """Render a single line with given font/color — for headings."""
        tk.Label(
            self.parent,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            wraplength=self.wraplength,
            justify=tk.LEFT,
            anchor=tk.W,
            pady=pady[0]
        ).pack(fill=tk.X, anchor=tk.W)

    def _render_bullet(self, text, bg, prefix="•"):
        """Render a bullet or numbered list item."""
        c = self.theme.colors
        f = self.theme.font

        row = tk.Frame(self.parent, bg=bg)
        row.pack(fill=tk.X, anchor=tk.W, pady=1)

        # Prefix
        tk.Label(
            row,
            text=prefix,
            bg=bg,
            fg=c["accent_primary"],
            font=f("body_bold"),
            width=3,
            anchor=tk.W
        ).pack(side=tk.LEFT, anchor=tk.NW, padx=(4, 2))

        # Text — may have inline markup
        has_markup = "**" in text or "`" in text
        if has_markup:
            inner = tk.Frame(row, bg=bg)
            inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
            renderer = MarkdownRenderer(
                inner, self.theme,
                wraplength=self.wraplength - 30,
                bg=bg
            )
            renderer._render_inline_rich(text, bg)
        else:
            tk.Label(
                row,
                text=text,
                bg=bg,
                fg=c["text_ethica"],
                font=f("body"),
                wraplength=self.wraplength - 30,
                justify=tk.LEFT,
                anchor=tk.W
            ).pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)

    def _render_code_block(self, code, bg):
        """Render a fenced code block — monospace, distinct background."""
        c = self.theme.colors
        f = self.theme.font

        # Code block frame — slightly different bg
        code_frame = tk.Frame(
            self.parent,
            bg=c["bg_primary"],
            padx=8,
            pady=6,
            relief=tk.FLAT
        )
        code_frame.pack(fill=tk.X, anchor=tk.W, pady=4)

        # Left accent bar
        tk.Frame(
            code_frame,
            bg=c["accent_soft"],
            width=3
        ).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        # Code text
        tk.Label(
            code_frame,
            text=code,
            bg=c["bg_primary"],
            fg=c["accent_bright"],
            font=f("mono"),
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=self.wraplength - 20
        ).pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)

    def _render_inline_rich(self, text, bg):
        """
        Render text with inline **bold** and `code` markup
        using a Text widget with named tags.
        """
        c = self.theme.colors
        f = self.theme.font

        # Measure approximate height needed
        approx_lines = max(1, len(text) // 60 + text.count("\n") + 1)

        widget = tk.Text(
            self.parent,
            bg=bg,
            fg=c["text_ethica"],
            font=f("body"),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            width=1,
            height=approx_lines,
            cursor="arrow",
            state=tk.NORMAL,
            highlightthickness=0,
            padx=0,
            pady=1,
            exportselection=False
        )
        widget.pack(fill=tk.X, anchor=tk.W)

        # Configure tags
        widget.tag_configure(
            "bold",
            font=f("body_bold"),
            foreground=c["text_primary"]
        )
        widget.tag_configure(
            "code",
            font=f("mono"),
            foreground=c["accent_bright"],
            background=c["bg_primary"]
        )
        widget.tag_configure(
            "normal",
            font=f("body"),
            foreground=c["text_ethica"]
        )

        # Parse and insert inline segments
        self._insert_inline(widget, text)

        # Recalculate height after insert
        actual_lines = int(widget.index(tk.END).split(".")[0])
        widget.config(
            height=max(1, actual_lines - 1),
            state=tk.NORMAL
        )

        # Expand width to fill
        widget.pack_configure(fill=tk.X, expand=True)

    def _insert_inline(self, widget, text):
        """
        Parse inline **bold** and `code` and insert into Text widget
        with appropriate tags.
        """
        # Pattern: **bold** or `code`
        pattern = re.compile(r'(\*\*(.+?)\*\*|`(.+?)`)')
        last_end = 0

        for match in pattern.finditer(text):
            # Normal text before match
            if match.start() > last_end:
                widget.insert(tk.END, text[last_end:match.start()], "normal")

            full = match.group(0)
            if full.startswith("**"):
                # Bold
                widget.insert(tk.END, match.group(2), "bold")
            elif full.startswith("`"):
                # Inline code
                widget.insert(tk.END, match.group(3), "code")

            last_end = match.end()

        # Remaining normal text
        if last_end < len(text):
            widget.insert(tk.END, text[last_end:], "normal")
