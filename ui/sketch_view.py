# ============================================================
# Ethica v0.1 — sketch_view.py
# Hybrid Sketching Canvas Tab
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Freehand soul. Shapes when thought crystallizes.
# Ethica can push annotations and concepts here.
# V draws, thinks, connects.
#
# Tools:
#   Pen      — freehand draw
#   Eraser   — erase strokes
#   Text     — click to place a text label
#   Shape    — rectangle, ellipse, arrow
#   Select   — move/delete elements
#   Clear    — wipe the surface
#
# Persistence: serialized as JSON in CanvasTab.content
# ============================================================

import logging
import tkinter as tk
from tkinter import simpledialog, colorchooser
import json
from datetime import datetime


# ── Default Colors ────────────────────────────────────────────

DEFAULT_PEN_COLOR   = "#c084fc"   # accent purple
DEFAULT_TEXT_COLOR  = "#e2d4f0"
DEFAULT_SHAPE_COLOR = "#7c3aed"
CANVAS_BG           = "#0f0a1a"   # deep dark


class SketchElement:
    """Base for all sketch elements."""
    def __init__(self, kind):
        self.kind  = kind
        self.id    = None   # tkinter canvas item id


class StrokeElement(SketchElement):
    def __init__(self, points, color, width):
        super().__init__("stroke")
        self.points = points   # flat list [x1,y1,x2,y2,...]
        self.color  = color
        self.width  = width

    def to_dict(self):
        return {"kind": "stroke", "points": self.points,
                "color": self.color, "width": self.width}

    @classmethod
    def from_dict(cls, d):
        return cls(d["points"], d["color"], d["width"])


class TextElement(SketchElement):
    def __init__(self, x, y, text, color, size=13):
        super().__init__("text")
        self.x     = x
        self.y     = y
        self.text  = text
        self.color = color
        self.size  = size

    def to_dict(self):
        return {"kind": "text", "x": self.x, "y": self.y,
                "text": self.text, "color": self.color, "size": self.size}

    @classmethod
    def from_dict(cls, d):
        return cls(d["x"], d["y"], d["text"], d["color"], d.get("size", 13))


class ShapeElement(SketchElement):
    def __init__(self, shape, x1, y1, x2, y2, color, width=2, filled=False):
        super().__init__("shape")
        self.shape  = shape   # "rect", "ellipse", "arrow"
        self.x1     = x1
        self.y1     = y1
        self.x2     = x2
        self.y2     = y2
        self.color  = color
        self.width  = width
        self.filled = filled

    def to_dict(self):
        return {"kind": "shape", "shape": self.shape,
                "x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2,
                "color": self.color, "width": self.width, "filled": self.filled}

    @classmethod
    def from_dict(cls, d):
        return cls(d["shape"], d["x1"], d["y1"], d["x2"], d["y2"],
                   d["color"], d.get("width", 2), d.get("filled", False))


class SketchView:
    """
    Hybrid sketch surface — freehand + shapes + text.
    Rendered inside a canvas tab frame.
    """

    TOOLS = ["pen", "eraser", "text", "rect", "ellipse", "arrow", "select"]

    def __init__(self, parent, theme, on_change=None):
        self.parent    = parent
        self.theme     = theme
        self.on_change = on_change

        self._elements   = []      # all sketch elements
        self._undo_stack = []      # for undo
        self._frame      = None
        self._canvas     = None

        # Tool state
        self._tool        = "pen"
        self._pen_color   = DEFAULT_PEN_COLOR
        self._pen_width   = 2
        self._shape_color = DEFAULT_SHAPE_COLOR
        self._text_color  = DEFAULT_TEXT_COLOR

        # Drawing state
        self._drawing     = False
        self._current_pts = []
        self._drag_start  = None
        self._preview_id  = None   # temp shape preview while dragging

        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        c = self.theme.colors
        f = self.theme.font

        self._frame = tk.Frame(self.parent, bg=c["bg_primary"])
        self._frame.pack(fill=tk.BOTH, expand=True)

        # ── Toolbar ───────────────────────────────────────────
        self._toolbar = tk.Frame(self._frame, bg=c["bg_secondary"], pady=4)
        self._toolbar.pack(fill=tk.X)

        self._tool_buttons = {}
        tools = [
            ("✏", "pen",     "Pen"),
            ("⌫", "eraser",  "Eraser"),
            ("T", "text",    "Text"),
            ("▭", "rect",    "Rectangle"),
            ("○", "ellipse", "Ellipse"),
            ("→", "arrow",   "Arrow"),
            ("↖", "select",  "Select"),
        ]

        for icon, tool, tip in tools:
            btn = tk.Button(
                self._toolbar,
                text=icon,
                width=2,
                bg=c["accent_soft"] if tool == "pen" else c["bg_secondary"],
                fg=c["accent_bright"] if tool == "pen" else c["text_muted"],
                font=f("body"),
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda t=tool: self._set_tool(t)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self._tool_buttons[tool] = btn

        # Separator
        tk.Frame(self._toolbar, bg=c["bg_tertiary"], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=6, pady=2
        )

        # Color picker
        self._color_swatch = tk.Button(
            self._toolbar,
            bg=self._pen_color,
            width=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self._pick_color
        )
        self._color_swatch.pack(side=tk.LEFT, padx=2)

        # Stroke width
        tk.Label(
            self._toolbar,
            text="W:",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small")
        ).pack(side=tk.LEFT, padx=(6, 0))

        self._width_var = tk.IntVar(value=2)
        width_spin = tk.Spinbox(
            self._toolbar,
            from_=1, to=20,
            textvariable=self._width_var,
            width=3,
            bg=c["bg_input"],
            fg=c["text_primary"],
            font=f("small"),
            relief=tk.FLAT,
            command=self._on_width_change
        )
        width_spin.pack(side=tk.LEFT, padx=2)

        # Separator
        tk.Frame(self._toolbar, bg=c["bg_tertiary"], width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=6, pady=2
        )

        # Undo
        tk.Button(
            self._toolbar,
            text="↩ Undo",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._undo
        ).pack(side=tk.LEFT, padx=2)

        # Clear
        tk.Button(
            self._toolbar,
            text="✕ Clear",
            bg=c["bg_secondary"],
            fg=c["text_muted"],
            font=f("small"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._clear_all
        ).pack(side=tk.LEFT, padx=2)

        # ── Drawing surface ───────────────────────────────────
        self._canvas = tk.Canvas(
            self._frame,
            bg=CANVAS_BG,
            highlightthickness=0,
            cursor="crosshair"
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",       self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<Double-Button-1>", self._on_double_click)

    # ── Tool Management ───────────────────────────────────────

    def _set_tool(self, tool):
        c = self.theme.colors
        # Reset all buttons
        for t, btn in self._tool_buttons.items():
            btn.config(
                bg=c["bg_secondary"],
                fg=c["text_muted"]
            )
        # Highlight active
        self._tool_buttons[tool].config(
            bg=c["accent_soft"],
            fg=c["accent_bright"]
        )
        self._tool = tool
        cursor = "crosshair"
        if tool == "eraser":
            cursor = "dotbox"
        elif tool == "text":
            cursor = "xterm"
        elif tool == "select":
            cursor = "fleur"
        self._canvas.config(cursor=cursor)

    def _pick_color(self):
        color = colorchooser.askcolor(
            color=self._pen_color,
            parent=self._frame,
            title="Choose color"
        )
        if color and color[1]:
            self._pen_color   = color[1]
            self._shape_color = color[1]
            self._text_color  = color[1]
            self._color_swatch.config(bg=color[1])

    def _on_width_change(self):
        self._pen_width = self._width_var.get()

    # ── Drawing Events ────────────────────────────────────────

    def _on_press(self, event):
        x, y = event.x, event.y
        self._drawing   = True
        self._drag_start = (x, y)

        if self._tool == "pen":
            self._current_pts = [x, y]

        elif self._tool == "eraser":
            self._erase_at(x, y)

        elif self._tool == "text":
            self._place_text(x, y)
            self._drawing = False

    def _on_drag(self, event):
        x, y = event.x, event.y
        if not self._drawing:
            return

        if self._tool == "pen":
            self._current_pts.extend([x, y])
            if len(self._current_pts) >= 4:
                pts = self._current_pts[-4:]
                self._canvas.create_line(
                    *pts,
                    fill=self._pen_color,
                    width=self._pen_width,
                    smooth=True,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                    tags="stroke_preview"
                )

        elif self._tool == "eraser":
            self._erase_at(x, y)

        elif self._tool in ("rect", "ellipse", "arrow"):
            # Preview shape
            if self._preview_id:
                self._canvas.delete(self._preview_id)
            sx, sy = self._drag_start
            self._preview_id = self._draw_shape_on_canvas(
                self._tool, sx, sy, x, y,
                self._shape_color, self._pen_width
            )

    def _on_release(self, event):
        x, y = event.x, event.y
        if not self._drawing:
            return
        self._drawing = False

        if self._tool == "pen":
            self._canvas.delete("stroke_preview")
            if len(self._current_pts) >= 4:
                elem = StrokeElement(
                    list(self._current_pts),
                    self._pen_color,
                    self._pen_width
                )
                elem.id = self._canvas.create_line(
                    *self._current_pts,
                    fill=self._pen_color,
                    width=self._pen_width,
                    smooth=True,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND
                )
                self._elements.append(elem)
                self._undo_stack.append(elem)
                self._notify_change()
            self._current_pts = []

        elif self._tool in ("rect", "ellipse", "arrow"):
            if self._preview_id:
                self._canvas.delete(self._preview_id)
                self._preview_id = None
            sx, sy = self._drag_start
            if abs(x - sx) > 5 or abs(y - sy) > 5:
                elem = ShapeElement(
                    self._tool, sx, sy, x, y,
                    self._shape_color, self._pen_width
                )
                elem.id = self._draw_shape_on_canvas(
                    self._tool, sx, sy, x, y,
                    self._shape_color, self._pen_width
                )
                self._elements.append(elem)
                self._undo_stack.append(elem)
                self._notify_change()

    def _on_double_click(self, event):
        """Double click to place text in text mode."""
        if self._tool == "text":
            self._place_text(event.x, event.y)

    # ── Drawing Helpers ───────────────────────────────────────

    def _draw_shape_on_canvas(self, shape, x1, y1, x2, y2, color, width):
        if shape == "rect":
            return self._canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=color, width=width, fill=""
            )
        elif shape == "ellipse":
            return self._canvas.create_oval(
                x1, y1, x2, y2,
                outline=color, width=width, fill=""
            )
        elif shape == "arrow":
            return self._canvas.create_line(
                x1, y1, x2, y2,
                fill=color, width=width,
                arrow=tk.LAST,
                arrowshape=(12, 15, 5)
            )

    def _place_text(self, x, y):
        """Open dialog and place text at position."""
        text = simpledialog.askstring(
            "Add Text",
            "Enter text:",
            parent=self._frame
        )
        if text and text.strip():
            elem = TextElement(x, y, text.strip(), self._text_color)
            elem.id = self._canvas.create_text(
                x, y,
                text=text.strip(),
                fill=self._text_color,
                font=("Inter", elem.size),
                anchor=tk.NW
            )
            self._elements.append(elem)
            self._undo_stack.append(elem)
            self._notify_change()

    def _erase_at(self, x, y):
        """Erase elements near cursor."""
        r = 12  # eraser radius
        items = self._canvas.find_overlapping(x-r, y-r, x+r, y+r)
        for item in items:
            # Find matching element
            for elem in list(self._elements):
                if elem.id == item:
                    self._canvas.delete(item)
                    self._elements.remove(elem)
                    self._notify_change()
                    break

    # ── Undo / Clear ──────────────────────────────────────────

    def _undo(self):
        if not self._undo_stack:
            return
        elem = self._undo_stack.pop()
        if elem.id:
            self._canvas.delete(elem.id)
        if elem in self._elements:
            self._elements.remove(elem)
        self._notify_change()

    def _clear_all(self):
        self._canvas.delete(tk.ALL)
        self._elements.clear()
        self._undo_stack.clear()
        self._notify_change()

    # ── Load / Dump ───────────────────────────────────────────

    def load(self, content):
        """Load sketch from CanvasTab.content JSON."""
        self._canvas.delete(tk.ALL)
        self._elements.clear()
        self._undo_stack.clear()

        if not content or not content.strip().startswith("{"):
            return

        try:
            data = json.loads(content)
            for d in data.get("elements", []):
                kind = d.get("kind")
                if kind == "stroke":
                    elem = StrokeElement.from_dict(d)
                    elem.id = self._canvas.create_line(
                        *elem.points,
                        fill=elem.color,
                        width=elem.width,
                        smooth=True,
                        capstyle=tk.ROUND,
                        joinstyle=tk.ROUND
                    )
                elif kind == "text":
                    elem = TextElement.from_dict(d)
                    elem.id = self._canvas.create_text(
                        elem.x, elem.y,
                        text=elem.text,
                        fill=elem.color,
                        font=("Inter", elem.size),
                        anchor=tk.NW
                    )
                elif kind == "shape":
                    elem = ShapeElement.from_dict(d)
                    elem.id = self._draw_shape_on_canvas(
                        elem.shape, elem.x1, elem.y1, elem.x2, elem.y2,
                        elem.color, elem.width
                    )
                else:
                    continue
                self._elements.append(elem)
        except Exception as e:
            logging.warning("[SketchView] Load error: %s", e)

    def dump(self):
        """Serialize to JSON for CanvasTab.content."""
        return json.dumps({
            "type":     "sketch",
            "updated":  datetime.now().isoformat(),
            "elements": [e.to_dict() for e in self._elements]
        }, indent=2)

    @classmethod
    def is_sketch_content(cls, content):
        if not content or not content.strip().startswith("{"):
            return False
        try:
            return json.loads(content).get("type") == "sketch"
        except Exception:
            return False

    # ── Ethica Push ───────────────────────────────────────────

    def add_annotation_from_ethica(self, text, x=None, y=None):
        """
        Ethica drops a text annotation onto the sketch surface.
        Positioned automatically if no coords given.
        """
        if x is None or y is None:
            # Stack annotations down the left side
            offset = len([e for e in self._elements if e.kind == "text"]) * 28
            x, y = 20, 20 + offset

        elem = TextElement(x, y, f"✦ {text}", DEFAULT_PEN_COLOR, size=12)
        elem.id = self._canvas.create_text(
            x, y,
            text=elem.text,
            fill=DEFAULT_PEN_COLOR,
            font=("Inter", 12),
            anchor=tk.NW
        )
        self._elements.append(elem)
        self._notify_change()

    # ── Helpers ───────────────────────────────────────────────

    def _notify_change(self):
        if self.on_change:
            self.on_change()

    def destroy(self):
        if self._frame:
            try:
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None
