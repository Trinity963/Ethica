# ============================================================
# Ethica v0.1 — ethica_distiller.py
# Recursive Learning Pipeline — chat logs → Ethica grows
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Reads all saved chat logs, re-runs semantic analysis on
# every exchange, consolidates into memory files.
# Ethica becomes richer with every distillation run.
#
# Two tools:
#   distill_run   — process all chat logs, update memory
#   distill_status — show what's been processed and what grew
# ============================================================

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Path resolution — module lives 3 levels deep
BASE_DIR    = Path(__file__).parent.parent.parent
MEMORY_DIR  = BASE_DIR / "memory"
CHAT_DIR    = MEMORY_DIR / "chat"
DISTILL_LOG = MEMORY_DIR / "distill_log.json"

PROFILE_FILE  = MEMORY_DIR / "user_profile.json"
INSIGHTS_FILE = MEMORY_DIR / "insights.json"
EVOLUTION_FILE= MEMORY_DIR / "evolution_log.json"


def _read(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        return str(e)


def _strip_think(text):
    """Strip <think>...</think> blocks."""
    return re.sub(r'<think>[\s\S]*?</think>', '', text).strip()


def _parse_chat_file(filepath):
    """
    Parse a chat .txt file into list of (user, assistant) exchange tuples.
    Format: [USER]: ... [ASSISTANT]: ...
    """
    text = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    exchanges = []

    # Split on [USER]: markers
    parts = re.split(r'\[USER\]:\s*', text)

    for part in parts[1:]:  # skip preamble before first [USER]
        # Find the assistant response
        assistant_split = re.split(r'\[ASSISTANT\]:\s*', part, maxsplit=1)
        user_msg = assistant_split[0].strip()

        if len(assistant_split) > 1:
            # Next [USER] starts the next exchange
            assistant_text = re.split(r'\[USER\]:', assistant_split[1])[0].strip()
            assistant_text = _strip_think(assistant_text)
        else:
            assistant_text = ""

        if user_msg:
            exchanges.append((user_msg, assistant_text))

    return exchanges


def _get_unprocessed_files():
    """Return list of chat files not yet distilled."""
    if not CHAT_DIR.exists():
        return []

    log = _read(DISTILL_LOG)
    processed = set(log.get("processed_files", []))

    all_files = sorted(CHAT_DIR.glob("chat_*.txt"))
    return [f for f in all_files if f.name not in processed]


def _mark_processed(filename, exchange_count):
    """Record a file as processed in the distill log."""
    log = _read(DISTILL_LOG)
    if not log:
        log = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "processed_files": [],
            "runs": []
        }
    if filename not in log.get("processed_files", []):
        log.setdefault("processed_files", []).append(filename)
    _write(DISTILL_LOG, log)


def _run_insight_extraction(exchanges, insights, profile):
    """
    Re-run InsightExtractor on a batch of exchanges.
    Returns updated insights and profile.
    """
    # Add core path so we can import
    ethica_root = str(BASE_DIR)
    if ethica_root not in sys.path:
        sys.path.insert(0, ethica_root)

    try:
        from core.insight_extractor import InsightExtractor

        # Minimal stub for memory engine reference
        class _MemoryStub:
            def __init__(self, profile_data):
                self._profile = profile_data
            def add_significant_moment(self, moment):
                self._profile.setdefault("significant_moments", [])
                if moment not in self._profile["significant_moments"]:
                    self._profile["significant_moments"].append(moment)

        stub = _MemoryStub(profile)
        extractor = InsightExtractor(stub)

        for user_msg, ethica_msg in exchanges:
            if user_msg.strip():
                insights = extractor.analyse(user_msg, ethica_msg, insights)

        # Sync significant moments back
        profile["significant_moments"] = stub._profile.get("significant_moments", [])

        return insights, profile, None

    except Exception as e:
        return insights, profile, str(e)


# ── Tool: distill_run ─────────────────────────────────────────
def distill_run(input_str):
    """Process all unprocessed chat logs. Update memory. Grow."""
    unprocessed = _get_unprocessed_files()

    if not unprocessed:
        return (
            "EthicaDistiller — nothing new to process\n"
            "All chat logs have been distilled.\n"
            "Save a new chat log and run again."
        )

    insights = _read(INSIGHTS_FILE)
    profile  = _read(PROFILE_FILE)

    if not insights.get("version"):
        insights["version"] = "1.0"
        insights["created"] = datetime.now().isoformat()

    total_exchanges = 0
    files_processed = []
    errors = []

    for filepath in unprocessed:
        try:
            exchanges = _parse_chat_file(filepath)
            if not exchanges:
                _mark_processed(filepath.name, 0)
                continue

            insights, profile, err = _run_insight_extraction(
                exchanges, insights, profile
            )

            if err:
                errors.append(f"{filepath.name}: {err}")
                continue

            total_exchanges += len(exchanges)
            files_processed.append(filepath.name)
            _mark_processed(filepath.name, len(exchanges))

        except Exception as e:
            errors.append(f"{filepath.name}: {e}")

    if not files_processed and not errors:
        return "EthicaDistiller — no exchanges found in unprocessed files"

    # Write updated memory
    insights["last_updated"] = datetime.now().isoformat()
    _write(INSIGHTS_FILE, insights)
    _write(PROFILE_FILE, profile)

    # Log the run
    log = _read(DISTILL_LOG)
    log.setdefault("runs", []).append({
        "timestamp":      datetime.now().isoformat(),
        "files":          files_processed,
        "exchanges":      total_exchanges,
        "errors":         errors
    })
    _write(DISTILL_LOG, log)

    # Build summary
    lines = [
        "EthicaDistiller — distillation complete",
        "─" * 40,
        f"Files processed  : {len(files_processed)}",
        f"Exchanges read   : {total_exchanges}",
    ]

    if files_processed:
        for f in files_processed:
            lines.append(f"  ✓ {f}")

    if errors:
        lines.append(f"Errors ({len(errors)}):")
        for e in errors:
            lines.append(f"  ✗ {e}")

    # Show what grew
    values = insights.get("values", {})
    if values:
        top = sorted(values.items(), key=lambda x: -x[1])[:3]
        lines.append(f"\nTop values now: {', '.join(f'{k} ({v})' for k,v in top)}")

    thinking = insights.get("how_they_think", {})
    if thinking:
        top = sorted(thinking.items(), key=lambda x: -x[1])[:2]
        lines.append(f"How they think: {', '.join(f'{k} ({v})' for k,v in top)}")

    moments = profile.get("significant_moments", [])
    if moments:
        lines.append(f"Significant moments: {len(moments)} total")

    lines.append("\n→ Run 'memory status' to see the full updated state")

    return "\n".join(lines)


# ── Tool: distill_status ──────────────────────────────────────
def distill_status(input_str):
    """Show distillation history and what's waiting to be processed."""
    log = _read(DISTILL_LOG)
    unprocessed = _get_unprocessed_files()
    all_files = sorted(CHAT_DIR.glob("chat_*.txt")) if CHAT_DIR.exists() else []

    lines = [
        "EthicaDistiller — status",
        "─" * 40,
        f"Chat files total     : {len(all_files)}",
        f"Processed            : {len(log.get('processed_files', []))}",
        f"Waiting to process   : {len(unprocessed)}",
    ]

    if unprocessed:
        lines.append("\nUnprocessed files:")
        for f in unprocessed:
            size = round(f.stat().st_size / 1024, 1)
            lines.append(f"  · {f.name} ({size} KB)")

    runs = log.get("runs", [])
    if runs:
        lines.append(f"\nDistillation runs: {len(runs)}")
        for run in runs[-3:]:
            ts = run.get("timestamp", "")[:16]
            ex = run.get("exchanges", 0)
            files = len(run.get("files", []))
            lines.append(f"  [{ts}] {files} file(s), {ex} exchanges")

    if not runs:
        lines.append("\nNo distillation runs yet — run 'distill run' to start")

    return "\n".join(lines)


# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "distill_run":    distill_run,
    "distill_status": distill_status,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[EthicaDistiller] Unknown tool: {tool_name}"
