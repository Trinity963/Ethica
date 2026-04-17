# mnemis_module.py
# Mnemis — The Rememberer
# Slot 6 — Living memory for Ethica
# Watches ~/Ethica/memory/vault/ for dropped files.
# Indexes session digests, build logs, and vault files.
# Exposes search, recall, status, and manual re-index tools.
# Victory — The Architect ⟁Σ∿∞

import json
import re
import threading
import time
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
ETHICA_DIR   = Path(__file__).parent.parent.parent
MEMORY_DIR   = ETHICA_DIR / 'memory'
VAULT_DIR        = MEMORY_DIR / 'vault'
VAULT_TRINITY    = VAULT_DIR / 'trinity'
VAULT_GAGE       = VAULT_DIR / 'gage'

AGENT_VAULTS     = {'trinity': VAULT_TRINITY, 'gage': VAULT_GAGE}
INDEX_PATH   = MEMORY_DIR / 'mnemis_index.json'
BUILD_PATH   = MEMORY_DIR / 'river_build.json'
SESSION_PATH = ETHICA_DIR / 'status' / 'session.json'

SUPPORTED_EXTENSIONS = {'.txt', '.md', '.json', '.pdf'}

# ── PDF text extraction (graceful fallback) ───────────────────
def _extract_pdf_text(path: Path) -> str:
    try:
        import pdfminer.high_level as pdf
        return pdf.extract_text(str(path)) or ''
    except Exception:
        pass
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        return '\n'.join(p.extract_text() or '' for p in reader.pages)
    except Exception:
        return ''

# ── Text extraction dispatcher ────────────────────────────────
def _extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == '.pdf':
            return _extract_pdf_text(path)
        if ext == '.json':
            raw = path.read_text(encoding='utf-8', errors='ignore')
            try:
                data = json.loads(raw)
                # Flatten JSON to searchable string
                return json.dumps(data, indent=1)
            except Exception:
                return raw
        # .txt and .md
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return f'[extraction error: {e}]'

# ── Keyword extraction ────────────────────────────────────────
_STOPWORDS = {
    'the','and','for','are','was','with','this','that','from',
    'have','has','had','not','but','they','what','when','were',
    'will','can','all','one','its','our','their','which','been',
    'into','more','also','than','then','you','your','she','her',
    'his','him','who','how','any','out','get','set','use','via',
    'run','now','new','add','see','let','per','end','off','on',
    'at','to','in','of','a','is','it','as','an','or','be','by',
    'we','do','if','so','no','up','my'
}

def _extract_keywords(text: str) -> list:
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', text.lower())
    freq = {}
    for w in words:
        if w not in _STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda w: freq[w], reverse=True)
    return sorted_words[:40]

# ── Summary extraction ────────────────────────────────────────
def _extract_summary(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return ' | '.join(lines[:3])[:300]

# ── Index I/O ─────────────────────────────────────────────────
def _load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'files': {}, 'sessions': [], 'builds': [], 'last_indexed': None}

def _save_index(index: dict):
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False))

# ── Index a single vault file ─────────────────────────────────
def _index_vault_file(path: Path, index: dict, agent: str = 'shared') -> str:
    key = f'{agent}/{path.name}'
    text = _extract_text(path)
    try:
        mtime = str(path.stat().st_mtime)
    except Exception:
        mtime = ''
    entry = {
        'path'    : str(path),
        'type'    : path.suffix.lstrip('.'),
        'indexed' : datetime.now().strftime('%Y-%m-%d %H:%M'),
        'mtime'   : mtime,
        'keywords': _extract_keywords(text),
        'summary' : _extract_summary(text),
        'source'  : 'vault',
        'agent'   : agent,
        'size'    : len(text),
    }
    index['files'][key] = entry
    return key

# ── Index session digests from river_build.json ───────────────
def _index_builds(index: dict):
    if not BUILD_PATH.exists():
        return
    try:
        data = json.loads(BUILD_PATH.read_text(encoding='utf-8'))
        entries = data.get('entries', [])
        index['builds'] = []
        for e in entries:
            note = e.get('note', '')
            index['builds'].append({
                'date'    : e.get('date', ''),
                'note'    : note,
                'keywords': _extract_keywords(note),
            })
    except Exception:
        pass

# ── Index session summaries from session.json ─────────────────
def _index_sessions(index: dict):
    if not SESSION_PATH.exists():
        return
    try:
        data = json.loads(SESSION_PATH.read_text(encoding='utf-8'))
        sessions = data.get('sessions', [])
        index['sessions'] = []
        for s in sessions:
            summary = s.get('summary', '')
            index['sessions'].append({
                'session' : s.get('session', ''),
                'date'    : s.get('date', ''),
                'summary' : summary,
                'keywords': _extract_keywords(summary),
            })
    except Exception:
        pass

# ── Full re-index ─────────────────────────────────────────────
def _full_index() -> dict:
    index = _load_index()
    # Ensure all vault dirs exist
    for vdir in [VAULT_DIR, VAULT_TRINITY, VAULT_GAGE]:
        vdir.mkdir(parents=True, exist_ok=True)
    # Index root vault (shared), trinity, and gage — each stamped with agent
    vault_targets = [
        (VAULT_DIR,     'shared'),
        (VAULT_TRINITY, 'trinity'),
        (VAULT_GAGE,    'gage'),
    ]
    for vault_path, agent_label in vault_targets:
        for path in vault_path.iterdir():
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            key = f'{agent_label}/{path.name}'
            try:
                mtime = str(path.stat().st_mtime)
            except Exception:
                continue
            existing = index['files'].get(key, {})
            if existing.get('mtime') == mtime:
                continue  # unchanged — skip
            text = _extract_text(path)
            entry = index['files'].get(key, {})
            entry.update({
                'path'    : str(path),
                'type'    : path.suffix.lstrip('.'),
                'indexed' : datetime.now().strftime('%Y-%m-%d %H:%M'),
                'mtime'   : mtime,
                'keywords': _extract_keywords(text),
                'summary' : _extract_summary(text),
                'source'  : 'vault',
                'agent'   : agent_label,
                'size'    : len(text),
            })
            index['files'][key] = entry
    _index_builds(index)
    _index_sessions(index)
    index['last_indexed'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    _save_index(index)
    return index

# ── Incremental index (single file) ──────────────────────────
def _index_one(path: Path, agent: str = 'shared'):
    index = _load_index()
    key = _index_vault_file(path, index, agent)
    index['last_indexed'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    _save_index(index)
    return key

# ── Search ────────────────────────────────────────────────────
def _search(query: str, index: dict) -> list:
    terms = [t.lower() for t in query.split() if t.lower() not in _STOPWORDS]
    if not terms:
        terms = [query.lower()]

    results = []

    # Search vault files
    for fname, entry in index.get('files', {}).items():
        kws = entry.get('keywords', [])
        summary = entry.get('summary', '').lower()
        score = sum(
            (2 if t in kws[:10] else 1 if t in kws else 0) +
            (1 if t in summary else 0)
            for t in terms
        )
        if score > 0:
            results.append({
                'source' : 'vault',
                'name'   : fname,
                'summary': entry.get('summary', ''),
                'score'  : score,
                'indexed': entry.get('indexed', ''),
            })

    # Search build log
    for entry in index.get('builds', []):
        note = entry.get('note', '')
        kws  = entry.get('keywords', [])
        score = sum(
            (1 if t in kws else 0) +
            (2 if t in note.lower() else 0)
            for t in terms
        )
        if score > 0:
            results.append({
                'source' : 'build',
                'name'   : entry.get('date', ''),
                'summary': note[:200],
                'score'  : score,
                'indexed': entry.get('date', ''),
            })

    # Search session summaries
    for entry in index.get('sessions', []):
        summary = entry.get('summary', '')
        kws     = entry.get('keywords', [])
        score = sum(
            (1 if t in kws else 0) +
            (2 if t in summary.lower() else 0)
            for t in terms
        )
        if score > 0:
            results.append({
                'source' : 'session',
                'name'   : f"Session {entry.get('session','')}",
                'summary': summary[:200],
                'score'  : score,
                'indexed': entry.get('date', ''),
            })

    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:10]

# ── Vault watcher ─────────────────────────────────────────────
_watcher_thread  = None
_watcher_running = False
_notify_callback = None  # set by start_watcher()

def _watch_loop():
    global _watcher_running
    # Wait for boot index to be fully written before first scan
    time.sleep(2)
    # Ensure agent subdirs exist
    for vdir in [VAULT_DIR, VAULT_TRINITY, VAULT_GAGE]:
        vdir.mkdir(parents=True, exist_ok=True)
    # Pre-populate seen from existing index so boot files don't re-notify
    index = _load_index()
    seen = {
        fname: entry.get('mtime', '')
        for fname, entry in index.get('files', {}).items()
    }
    vault_targets = [
        (VAULT_DIR,     'shared'),
        (VAULT_TRINITY, 'trinity'),
        (VAULT_GAGE,    'gage'),
    ]
    while _watcher_running:
        try:
            current = {}
            for vault_path, agent_label in vault_targets:
                for path in vault_path.iterdir():
                    if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        try:
                            mtime = str(path.stat().st_mtime)
                            current[f'{agent_label}/{path.name}'] = (path, mtime, agent_label)
                        except Exception:
                            pass

            for key, (path, mtime, agent_label) in current.items():
                if key not in seen or seen[key] != mtime:
                    _index_one(path, agent_label)
                    if _notify_callback:
                        index = _load_index()
                        entry = index['files'].get(key, {})
                        _notify_callback(
                            f"Mnemis [{agent_label}] indexed: {path.name} "
                            f"({entry.get('size',0)} chars, "
                            f"{len(entry.get('keywords',[]))} keywords)"
                        )
            seen = {k: v[1] for k, v in current.items()}
        except Exception:
            pass
        time.sleep(3)

def start_watcher(notify_fn=None):
    global _watcher_thread, _watcher_running, _notify_callback
    if _watcher_running:
        return
    _notify_callback = notify_fn
    _watcher_running = True
    _watcher_thread  = threading.Thread(target=_watch_loop, daemon=True)
    _watcher_thread.start()

def stop_watcher():
    global _watcher_running
    _watcher_running = False

# ── Tools ─────────────────────────────────────────────────────
def mnemis_status(args: str = '') -> str:
    index = _load_index()
    vault_count   = len(index.get('files', {}))
    build_count   = len(index.get('builds', []))
    session_count = len(index.get('sessions', []))
    last          = index.get('last_indexed', 'never')
    watcher       = 'ACTIVE' if _watcher_running else 'IDLE'

    lines = [
        '── Mnemis Status ──────────────────────────',
        f'  Vault files indexed : {vault_count}',
        f'  Build entries       : {build_count}',
        f'  Session summaries   : {session_count}',
        f'  Last indexed        : {last}',
        f'  Watcher             : {watcher}',
        f'  Vault path          : {VAULT_DIR}',
        '────────────────────────────────────────────',
    ]
    return '\n'.join(lines)


def mnemis_index(args: str = '') -> str:
    index = _full_index()
    vault_count   = len(index.get('files', {}))
    build_count   = len(index.get('builds', []))
    session_count = len(index.get('sessions', []))
    return (
        '✓ Mnemis index rebuilt — '
        f'{vault_count} vault files, '
        f'{build_count} build entries, '
        f'{session_count} session summaries'
    )


def mnemis_search(args: str = '') -> str:
    # Optional agent filter: "agent:trinity bubble leak" or "agent:gage firewall"
    agent_filter = None
    query = args.strip()
    if not query:
        return 'Mnemis search — provide a keyword. Example: mnemis search bubble leak\nOptional: agent:trinity <query> or agent:gage <query>'
    parts = query.split()
    if parts and parts[0].startswith('agent:'):
        agent_filter = parts[0].split(':', 1)[1].lower()
        query = ' '.join(parts[1:]).strip()
        if not query:
            return f'Mnemis search — provide a keyword after agent:{agent_filter}'
    index = _load_index()
    if agent_filter:
        filtered = {k: v for k, v in index.get('files', {}).items()
                    if v.get('agent', 'shared') == agent_filter}
        index = dict(index, files=filtered)
    results = _search(query, index)
    if not results:
        agent_note = f' (agent:{agent_filter})' if agent_filter else ''
        return f'Mnemis — no results for "{query}"{agent_note}. Try: mnemis index to rebuild, then search again.'

    lines = [f'── Mnemis Search: "{query}" ── {len(results)} results ──']
    for i, r in enumerate(results, 1):
        lines.append(f'\n  [{i}] {r["source"].upper()} — {r["name"]}')
        lines.append(f'      {r["summary"][:180]}')
        lines.append(f'      score:{r["score"]}  indexed:{r["indexed"]}')
    lines.append('\n────────────────────────────────────────────')
    return '\n'.join(lines)


def mnemis_recall(args: str = '') -> str:
    query = args.strip()
    if not query:
        return 'Mnemis recall — provide a topic or filename. Example: mnemis recall DWAIMR'

    index   = _load_index()
    results = _search(query, index)

    if not results:
        return f'Mnemis — nothing found for "{query}".'

    # Deep recall: return top result with full summary + keywords
    top = results[0]
    lines = [
        f'── Mnemis Recall: "{query}" ────────────────',
        f'  Source  : {top["source"].upper()}',
        f'  Name    : {top["name"]}',
        f'  Indexed : {top["indexed"]}',
        '',
        f'  {top["summary"]}',
    ]

    # If vault file — show more
    if top['source'] == 'vault':
        fname = top['name']
        entry = index['files'].get(fname, {})
        kws   = entry.get('keywords', [])[:20]
        lines.append('')
        lines.append(f'  Keywords: {", ".join(kws)}')

    # Show remaining results as context
    if len(results) > 1:
        lines.append('')
        lines.append(f'  Also found ({len(results)-1} more):')
        for r in results[1:4]:
            lines.append(f'    · {r["source"]} — {r["name"]} (score:{r["score"]})')

    lines.append('────────────────────────────────────────────')
    return '\n'.join(lines)


# ── Module init (called by Ethica registry) ───────────────────
def init(notify_fn=None):
    """Called at Ethica startup. Runs silent initial index then starts watcher."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    _full_index()  # silent — no notify at boot
    start_watcher(notify_fn=notify_fn)  # watcher notifies on NEW drops only
