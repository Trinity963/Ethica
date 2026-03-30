# ============================================================
# Ethica v0.1 — project_engine.py
# Project Task Engine
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Powers the Project canvas tab type.
# Tasks are stored as structured JSON inside the tab content.
# Ethica pushes tasks via [PROJECT: task] syntax.
# V checks them off, reorders, adds notes.
# ============================================================

import json
from datetime import datetime


# ── Task Status ───────────────────────────────────────────────

STATUS_TODO     = "todo"
STATUS_DOING    = "doing"
STATUS_DONE     = "done"
STATUS_BLOCKED  = "blocked"

STATUS_LABELS = {
    STATUS_TODO:    "○",
    STATUS_DOING:   "◉",
    STATUS_DONE:    "✓",
    STATUS_BLOCKED: "✗",
}

PRIORITY_LOW    = 1
PRIORITY_NORMAL = 2
PRIORITY_HIGH   = 3

PRIORITY_LABELS = {
    PRIORITY_LOW:    "↓",
    PRIORITY_NORMAL: "·",
    PRIORITY_HIGH:   "↑",
}


class Task:
    """A single project task."""

    _id_counter = 0

    def __init__(self, text, status=STATUS_TODO, priority=PRIORITY_NORMAL,
                 note="", created=None, task_id=None):
        Task._id_counter += 1
        self.id       = task_id or f"task_{Task._id_counter}"
        self.text     = text
        self.status   = status
        self.priority = priority
        self.note     = note
        self.created  = created or datetime.now().strftime("%b %d %H:%M")
        self.modified = self.created

    def to_dict(self):
        return {
            "id":       self.id,
            "text":     self.text,
            "status":   self.status,
            "priority": self.priority,
            "note":     self.note,
            "created":  self.created,
            "modified": self.modified,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            text     = d.get("text", ""),
            status   = d.get("status", STATUS_TODO),
            priority = d.get("priority", PRIORITY_NORMAL),
            note     = d.get("note", ""),
            created  = d.get("created"),
            task_id  = d.get("id"),
        )

    @property
    def status_icon(self):
        return STATUS_LABELS.get(self.status, "○")

    @property
    def priority_icon(self):
        return PRIORITY_LABELS.get(self.priority, "·")

    def cycle_status(self):
        """Cycle through: todo → doing → done → todo"""
        cycle = [STATUS_TODO, STATUS_DOING, STATUS_DONE]
        idx = cycle.index(self.status) if self.status in cycle else 0
        self.status = cycle[(idx + 1) % len(cycle)]
        self.modified = datetime.now().strftime("%b %d %H:%M")

    def cycle_priority(self):
        """Cycle through: normal → high → low → normal"""
        cycle = [PRIORITY_NORMAL, PRIORITY_HIGH, PRIORITY_LOW]
        idx = cycle.index(self.priority) if self.priority in cycle else 0
        self.priority = cycle[(idx + 1) % len(cycle)]
        self.modified = datetime.now().strftime("%b %d %H:%M")


class ProjectEngine:
    """
    Manages a list of tasks for a Project canvas tab.

    Content is serialized as JSON and stored in the CanvasTab.content field —
    same persistence system as document/code tabs, no new files needed.
    """

    def __init__(self):
        self.tasks = []
        self.title = "Project"
        self.description = ""

    # ── Serialization ─────────────────────────────────────────

    def to_json(self):
        """Serialize to JSON string — stored in CanvasTab.content"""
        return json.dumps({
            "type":        "project",
            "title":       self.title,
            "description": self.description,
            "tasks":       [t.to_dict() for t in self.tasks],
            "updated":     datetime.now().isoformat(),
        }, indent=2)

    @classmethod
    def from_json(cls, json_str):
        """Deserialize from CanvasTab.content string."""
        engine = cls()
        try:
            data = json.loads(json_str)
            engine.title       = data.get("title", "Project")
            engine.description = data.get("description", "")
            engine.tasks       = [Task.from_dict(t) for t in data.get("tasks", [])]
        except (json.JSONDecodeError, Exception):
            pass
        return engine

    @classmethod
    def is_project_content(cls, content):
        """Check if a tab's content is project JSON."""
        if not content or not content.strip().startswith("{"):
            return False
        try:
            data = json.loads(content)
            return data.get("type") == "project"
        except Exception:
            return False

    # ── Task Management ───────────────────────────────────────

    def add_task(self, text, priority=PRIORITY_NORMAL):
        """Add a new task. Returns the task."""
        task = Task(text=text.strip(), priority=priority)
        self.tasks.append(task)
        return task

    def add_tasks_from_push(self, push_text):
        """
        Parse Ethica's [PROJECT: ...] push content.
        Supports:
            Single task:  "Build the authentication module"
            Multiple:     "- Task one\n- Task two\n- Task three"
            Numbered:     "1. Task one\n2. Task two"
        Returns list of added tasks.
        """
        added = []
        lines = push_text.strip().splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Strip list markers
            for prefix in ["- ", "* ", "• "]:
                if line.startswith(prefix):
                    line = line[len(prefix):]
                    break
            # Strip numbered list markers
            if len(line) > 2 and line[0].isdigit() and line[1] in ".):":
                line = line[2:].strip()
            elif len(line) > 3 and line[:2].isdigit() and line[2] in ".):":
                line = line[3:].strip()

            if line:
                task = self.add_task(line)
                added.append(task)

        return added

    def remove_task(self, task_id):
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_task(self, task_id):
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def move_task_up(self, task_id):
        for i, t in enumerate(self.tasks):
            if t.id == task_id and i > 0:
                self.tasks[i], self.tasks[i-1] = self.tasks[i-1], self.tasks[i]
                return True
        return False

    def move_task_down(self, task_id):
        for i, t in enumerate(self.tasks):
            if t.id == task_id and i < len(self.tasks) - 1:
                self.tasks[i], self.tasks[i+1] = self.tasks[i+1], self.tasks[i]
                return True
        return False

    # ── Stats ─────────────────────────────────────────────────

    @property
    def stats(self):
        total  = len(self.tasks)
        done   = sum(1 for t in self.tasks if t.status == STATUS_DONE)
        doing  = sum(1 for t in self.tasks if t.status == STATUS_DOING)
        todo   = sum(1 for t in self.tasks if t.status == STATUS_TODO)
        pct    = int((done / total) * 100) if total > 0 else 0
        return {
            "total": total, "done": done,
            "doing": doing, "todo": todo,
            "percent": pct
        }
