# ============================================================
# Ethica v0.1 — git_tool.py
# Git Tool Module — sovereign git integration
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
# ============================================================

from pathlib import Path
import subprocess
import os

MODULE_DIR  = Path(__file__).parent
ETHICA_ROOT = MODULE_DIR.parent.parent

DEFAULT_REPO = str(ETHICA_ROOT)

def _run_git(args, repo_path):
    """Run a git command in a repo. Returns (stdout, stderr, returncode)."""
    repo = os.path.expanduser(repo_path.strip()) if repo_path.strip() else DEFAULT_REPO
    if not os.path.exists(repo):
        return None, f"Path not found: {repo}", 1
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return None, "git not found — install git first", 1
    except subprocess.TimeoutExpired:
        return None, "git command timed out", 1

# ── Tool: git_status ──────────────────────────────────────────
def git_status(input_str):
    repo = input_str.strip() or DEFAULT_REPO
    out, err, code = _run_git(["status"], repo)
    if code != 0:
        return f"Git Status — error:\n{err}"
    return f"Git Status — {os.path.expanduser(repo)}\n{'─'*40}\n{out}"

# ── Tool: git_log ─────────────────────────────────────────────
def git_log(input_str):
    repo = input_str.strip() or DEFAULT_REPO
    out, err, code = _run_git(
        ["log", "--oneline", "--graph", "--decorate", "-20"], repo
    )
    if code != 0:
        return f"Git Log — error:\n{err}"
    if not out.strip():
        return "Git Log — no commits yet."
    return f"Git Log — {os.path.expanduser(repo)}\n{'─'*40}\n{out}"

# ── Tool: git_diff ────────────────────────────────────────────
def git_diff(input_str):
    repo = input_str.strip() or DEFAULT_REPO
    out, err, code = _run_git(["diff", "--stat"], repo)
    if code != 0:
        return f"Git Diff — error:\n{err}"
    if not out.strip():
        return "Git Diff — no unstaged changes."
    # Also get the actual diff but truncated
    out2, _, _ = _run_git(["diff"], repo)
    diff_text = out2[:2000] + "\n... [truncated]" if out2 and len(out2) > 2000 else out2
    return f"Git Diff — {os.path.expanduser(repo)}\n{'─'*40}\n{out}\n{diff_text}"

# ── Tool: git_branch ──────────────────────────────────────────
def git_branch(input_str):
    repo = input_str.strip() or DEFAULT_REPO
    out, err, code = _run_git(["branch", "-a"], repo)
    if code != 0:
        return f"Git Branch — error:\n{err}"
    if not out.strip():
        return "Git Branch — no branches found."
    return f"Git Branch — {os.path.expanduser(repo)}\n{'─'*40}\n{out}"

# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "git_status": git_status,
    "git_log":    git_log,
    "git_diff":   git_diff,
    "git_branch": git_branch,
}
def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[GitTool] Unknown tool: {tool_name}"
