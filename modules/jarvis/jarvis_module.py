# ── J.A.R.V.I.S. — The Infiltrator ───────────────────────────
# Slot 7 — Pentesting & Vulnerability Intelligence
# Sovereign local CVE database, tool-agnostic recon.
# Portable by design — config-driven, no hard paths.
# Victory — The Architect ⟁Σ∿∞

import json
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / 'Ethica/config/jarvis_config.json'
DEFAULT_CVE_PATH = Path.home() / 'cvelistV5'
CVE_FORK_URL = 'https://github.com/Trinity963/cvelistV5.git'

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {
        'cve_path': str(DEFAULT_CVE_PATH),
        'fork_url': CVE_FORK_URL,
        'last_update': None,
        'tools_checked': {}
    }

def _save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def _cve_path(cfg: dict) -> Path:
    return Path(cfg.get('cve_path', str(DEFAULT_CVE_PATH)))

# ── Tool availability ─────────────────────────────────────────
RECON_TOOLS = ['nmap', 'gobuster', 'whatweb', 'nikto', 'curl', 'git']

def _check_tools() -> dict:
    results = {}
    for tool in RECON_TOOLS:
        result = subprocess.run(['which', tool], capture_output=True, text=True)
        results[tool] = result.stdout.strip() if result.returncode == 0 else None
    return results

# ── CVE helpers ───────────────────────────────────────────────
def _cve_db_exists(cfg: dict) -> bool:
    p = _cve_path(cfg)
    return (p / 'cves').exists()

def _search_cve_files(cve_dir: Path, query: str, max_results: int = 10) -> list:
    """Walk CVE JSON files and return matches for query."""
    query_lower = query.lower()
    results = []
    cve_root = cve_dir / 'cves'
    if not cve_root.exists():
        return results

    for json_file in sorted(cve_root.rglob('*.json'), reverse=True):
        if len(results) >= max_results:
            break
        try:
            raw = json_file.read_text(errors='ignore')
            if query_lower not in raw.lower():
                continue
            data = json.loads(raw)
            cve_id = data.get('cveMetadata', {}).get('cveId', json_file.stem)
            # Extract description
            desc = ''
            try:
                descs = data['containers']['cna'].get('descriptions', [])
                desc = descs[0].get('value', '')[:200] if descs else ''
            except Exception:
                pass
            # Extract severity
            severity = ''
            try:
                metrics = data['containers']['cna'].get('metrics', [])
                for m in metrics:
                    for k, v in m.items():
                        if 'cvss' in k.lower():
                            severity = v.get('baseSeverity', '')
                            break
            except Exception:
                pass
            results.append({
                'id': cve_id,
                'severity': severity,
                'description': desc,
                'file': str(json_file)
            })
        except Exception:
            continue
    return results

# ── Tool: jarvis_status ───────────────────────────────────────
def jarvis_status(args: str = '') -> str:
    cfg = _load_config()
    cve_p = _cve_path(cfg)
    db_exists = _cve_db_exists(cfg)
    last = cfg.get('last_update') or 'never'
    tools = _check_tools()

    lines = ['── J.A.R.V.I.S. Status ── The Infiltrator ──']
    lines.append(f'CVE database : {cve_p}')
    lines.append(f'DB present   : {"✓ yes" if db_exists else "✗ not found — run: jarvis setup"}')
    lines.append(f'Last update  : {last}')
    lines.append(f'Fork URL     : {cfg.get("fork_url", CVE_FORK_URL)}')
    lines.append('')
    lines.append('Recon tools:')
    for tool, path in tools.items():
        status = f'✓ {path}' if path else '✗ not installed'
        lines.append(f'  {tool:<12} {status}')
    return '\n'.join(lines)

# ── Tool: jarvis_setup ────────────────────────────────────────
def jarvis_setup(args: str = '') -> str:
    cfg = _load_config()
    cve_p = _cve_path(cfg)
    fork_url = cfg.get('fork_url', CVE_FORK_URL)

    if _cve_db_exists(cfg):
        return (f'✓ CVE database already present at {cve_p}\n'
                f'Run: jarvis update  to pull latest CVEs.')

    # Check git available
    git_check = subprocess.run(['which', 'git'], capture_output=True)
    if git_check.returncode != 0:
        return '✗ git not found — install git first: sudo apt install git'

    lines = [f'Cloning CVE database from {fork_url}']
    lines.append(f'Destination: {cve_p}')
    lines.append('This may take a few minutes — the CVE list is large...')

    try:
        result = subprocess.run(
            ['git', 'clone', '--depth=1', fork_url, str(cve_p)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            cfg['last_update'] = datetime.now().isoformat()
            _save_config(cfg)
            # Count CVEs
            cve_count = sum(1 for _ in (cve_p / 'cves').rglob('*.json'))
            lines.append(f'✓ Clone complete — {cve_count:,} CVE records indexed locally')
            lines.append(f'✓ Config saved to {CONFIG_PATH}')
            lines.append('Run: jarvis search <keyword>  to start hunting')
        else:
            lines.append(f'✗ Clone failed: {result.stderr[:300]}')
    except subprocess.TimeoutExpired:
        lines.append('✗ Clone timed out — try again or check connection')
    except Exception as e:
        lines.append(f'✗ Error: {e}')

    return '\n'.join(lines)

# ── Tool: jarvis_update ───────────────────────────────────────
def jarvis_update(args: str = '') -> str:
    cfg = _load_config()
    cve_p = _cve_path(cfg)

    if not _cve_db_exists(cfg):
        return '✗ CVE database not found — run: jarvis setup  first'

    try:
        result = subprocess.run(
            ['git', '-C', str(cve_p), 'pull', '--ff-only'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            cfg['last_update'] = datetime.now().isoformat()
            _save_config(cfg)
            output = result.stdout.strip()
            if 'Already up to date' in output:
                return f'✓ CVE database already up to date — last update: {cfg["last_update"]}'
            # Count new files mentioned
            new_files = output.count('.json')
            return (f'✓ CVE database updated — {new_files} records changed\n'
                    f'Last update: {cfg["last_update"]}\n'
                    f'{output[:300]}')
        else:
            return f'✗ Update failed:\n{result.stderr[:300]}'
    except subprocess.TimeoutExpired:
        return '✗ Update timed out — check connection'
    except Exception as e:
        return f'✗ Error: {e}'

# ── Tool: jarvis_search ───────────────────────────────────────
def jarvis_search(args: str = '') -> str:
    query = args.strip()
    if not query:
        return ('jarvis search — provide a keyword, product, or CVE ID\n'
                'Examples:\n'
                '  jarvis search apache log4j\n'
                '  jarvis search CVE-2021-44228\n'
                '  jarvis search remote code execution critical')

    cfg = _load_config()
    if not _cve_db_exists(cfg):
        return '✗ CVE database not found — run: jarvis setup  first'

    cve_p = _cve_path(cfg)

    # CVE-ID direct lookup
    cve_id_match = re.search(r'CVE-\d{4}-\d+', query, re.IGNORECASE)
    if cve_id_match:
        cve_id = cve_id_match.group(0).upper()
        year = cve_id.split('-')[1]
        prefix = cve_id.split('-')[2][:4].ljust(4, 'x')
        # Search directly
        results = _search_cve_files(cve_p, cve_id, max_results=1)
        if results:
            r = results[0]
            lines = [f'── {r["id"]} ── Severity: {r["severity"] or "unknown"} ──']
            lines.append(r['description'])
            lines.append(f'File: {r["file"]}')
            return '\n'.join(lines)
        return f'✗ {cve_id} not found in local database — run: jarvis update'

    # Keyword search
    results = _search_cve_files(cve_p, query, max_results=8)
    if not results:
        return (f'✗ No CVEs found matching "{query}"\n'
                f'Try: jarvis update  to refresh, then search again')

    lines = [f'── Jarvis Search: "{query}" — {len(results)} results ──']
    for i, r in enumerate(results, 1):
        sev = f'[{r["severity"]}]' if r['severity'] else '[?]'
        lines.append(f'\n  [{i}] {r["id"]} {sev}')
        lines.append(f'      {r["description"][:160]}')
    return '\n'.join(lines)

# ── Tool: jarvis_audit ────────────────────────────────────────
def jarvis_audit(args: str = '') -> str:
    target = args.strip()
    if not target:
        return ('jarvis audit — provide a file or directory path\n'
                'Example: jarvis audit /home/trinity/myapp/requirements.txt')

    target_path = Path(target)
    if not target_path.exists():
        return f'✗ Path not found: {target}'

    cfg = _load_config()
    if not _cve_db_exists(cfg):
        return '✗ CVE database not found — run: jarvis setup  first'

    # Extract version strings from file(s)
    files_to_scan = []
    if target_path.is_file():
        files_to_scan = [target_path]
    else:
        for ext in ['*.txt', '*.json', '*.xml', '*.cfg', '*.toml', '*.lock']:
            files_to_scan.extend(target_path.rglob(ext))

    if not files_to_scan:
        return f'✗ No scannable files found in {target}'

    # Extract package==version or package>=version patterns
    version_pattern = re.compile(
        r'([a-zA-Z][a-zA-Z0-9_\-\.]+)[>=<!~^]{1,2}([0-9][0-9a-zA-Z\.\-]*)'
    )

    found = {}
    for f in files_to_scan[:20]:  # cap at 20 files
        try:
            text = f.read_text(errors='ignore')
            for match in version_pattern.finditer(text):
                pkg, ver = match.group(1), match.group(2)
                found[pkg.lower()] = ver
        except Exception:
            continue

    if not found:
        return f'✗ No version strings detected in {target}'

    lines = [f'── J.A.R.V.I.S. Audit: {target} ──']
    lines.append(f'Packages detected: {len(found)}')
    lines.append('Searching CVE database...\n')

    hits = 0
    cve_p = _cve_path(cfg)
    for pkg, ver in list(found.items())[:15]:  # cap searches
        results = _search_cve_files(cve_p, pkg, max_results=2)
        if results:
            hits += 1
            lines.append(f'  ⚠ {pkg} {ver}')
            for r in results:
                sev = f'[{r["severity"]}]' if r['severity'] else '[?]'
                lines.append(f'    → {r["id"]} {sev} {r["description"][:120]}')

    if hits == 0:
        lines.append('✓ No CVE matches found for detected packages')
        lines.append('Note: Always verify against NVD for full coverage')
    else:
        lines.append(f'\n⚠ {hits} package(s) with potential CVE matches')
        lines.append('Verify severity and version applicability before acting')

    return '\n'.join(lines)

# ── Model detection ─────────────────────────────────────────
import requests as _requests

JARVIS_MODEL_PREFERENCE = [
    'whiterabbitneo',   # Easter egg — the infiltrator's secret weapon
    'codellama',
    'mistral',
    'deepseek-coder',
]

_PRIMARY_CONFIG_PATH = Path.home() / 'Ethica/config/settings.json'

def _get_primary_model() -> str:
    try:
        data = json.loads(_PRIMARY_CONFIG_PATH.read_text())
        return data.get('model', 'mistral')
    except Exception:
        return 'mistral'

def _get_ollama_host() -> str:
    try:
        data = json.loads(_PRIMARY_CONFIG_PATH.read_text())
        return data.get('ollama_host', 'http://localhost:11434')
    except Exception:
        return 'http://localhost:11434'

def _get_jarvis_model() -> str:
    cfg = _load_config()
    if cfg.get('model'):
        return cfg['model']
    host = _get_ollama_host()
    try:
        resp = _requests.get(f'{host}/api/tags', timeout=5)
        if resp.status_code == 200:
            available = [m['name'].lower() for m in resp.json().get('models', [])]
            for preferred in JARVIS_MODEL_PREFERENCE:
                for a in available:
                    if preferred in a:
                        return a
    except Exception:
        pass
    return _get_primary_model()

def _llm_query(prompt: str, system: str = '') -> str:
    host = _get_ollama_host()
    model = _get_jarvis_model()
    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})
    try:
        resp = _requests.post(
            f'{host}/api/chat',
            json={'model': model, 'messages': messages, 'stream': False},
            timeout=120
        )
        if resp.status_code == 200:
            return resp.json().get('message', {}).get('content', '').strip()
        return f'Model error: {resp.status_code}'
    except Exception as e:
        return f'LLM query failed: {e}'


# ── Tool: jarvis_analyze ─────────────────────────────────────
def jarvis_analyze(args: str = '') -> str:
    query = args.strip()
    if not query:
        return 'jarvis analyze — provide a CVE ID or keyword\nExample: jarvis analyze CVE-2021-44228'
    cfg = _load_config()
    model = _get_jarvis_model()
    cve_data = ''
    if _cve_db_exists(cfg):
        results = _search_cve_files(_cve_path(cfg), query, max_results=3)
        if results:
            parts = []
            for r in results:
                parts.append(f'CVE: {r["id"]} | Severity: {r["severity"] or "unknown"}')
                parts.append(f'Description: {r["description"]}')
                parts.append('')
            cve_data = '\n'.join(parts)
    system = (
        'You are J.A.R.V.I.S. — a sovereign local security intelligence agent. '
        'You assist with authorized penetration testing and bug bounty research. '
        'Provide technical, precise analysis. Be direct and useful.'
    )
    if cve_data:
        prompt = (
            f'Analyze the following CVE data for: {query}\n\n{cve_data}\n'
            f'Provide:\n'
            f'1. Attack vector and exploitability assessment\n'
            f'2. Affected conditions (versions, configs, exposure)\n'
            f'3. Suggested proof-of-concept approach (authorized testing)\n'
            f'4. Mitigation and patching priority\n'
            f'5. Bug bounty relevance'
        )
    else:
        prompt = (
            f'Analyze this security topic for authorized bug bounty research: {query}\n\n'
            f'1. Known attack vectors\n2. Common vulnerable configurations\n'
            f'3. Suggested testing approach\n4. Mitigation\n5. Bug bounty relevance'
        )
    header = f'J.A.R.V.I.S. Analysis: {query} | Model: {model}\n\n'
    return header + _llm_query(prompt, system)


# ── Tool: jarvis_recon ───────────────────────────────────────
def jarvis_recon(args: str = '') -> str:
    target = args.strip()
    if not target:
        return 'jarvis recon — provide a target URL or IP\nExample: jarvis recon https://example.com\nAuthorized targets only.'
    model = _get_jarvis_model()
    recon_data = [f'Target: {target}', f'Timestamp: {datetime.now().isoformat()}', '']
    try:
        resp = _requests.get(
            target if target.startswith('http') else f'http://{target}',
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Security Research)'},
            allow_redirects=True
        )
        recon_data.append(f'Status: {resp.status_code} | Final URL: {resp.url}')
        interesting = ['server','x-powered-by','x-frame-options','content-security-policy',
                       'strict-transport-security','x-content-type-options','set-cookie']
        for h in interesting:
            if h in resp.headers:
                recon_data.append(f'  {h}: {resp.headers[h][:120]}')
    except Exception as e:
        recon_data.append(f'HTTP fetch failed: {e}')
    nmap_check = subprocess.run(['which', 'nmap'], capture_output=True)
    if nmap_check.returncode == 0:
        try:
            nmap_target = target.replace('https://','').replace('http://','').split('/')[0]
            result = subprocess.run(['nmap','-F','--open', nmap_target],
                                    capture_output=True, text=True, timeout=30)
            recon_data.append(result.stdout[:800] if result.returncode == 0 else f'nmap error: {result.stderr[:200]}')
        except Exception as e:
            recon_data.append(f'nmap error: {e}')
    raw = '\n'.join(recon_data)
    system = (
        'You are J.A.R.V.I.S. — a sovereign local security intelligence agent. '
        'Analyze recon data for authorized bug bounty research. Be technical and direct.'
    )
    prompt = (
        f'Analyze this recon data for authorized bug bounty research:\n\n{raw}\n\n'
        f'1. Technology stack assessment\n'
        f'2. Security header analysis — missing or misconfigured\n'
        f'3. Open ports risk assessment\n'
        f'4. Likely attack surface\n'
        f'5. Bug bounty angle'
    )
    return f'J.A.R.V.I.S. Recon: {target} | Model: {model}\n\n{raw}\n\nAnalysis:\n' + _llm_query(prompt, system)


# ── Module registry ───────────────────────────────────────────
TOOLS = {
    'jarvis_status':  jarvis_status,
    'jarvis_setup':   jarvis_setup,
    'jarvis_update':  jarvis_update,
    'jarvis_search':  jarvis_search,
    'jarvis_audit':   jarvis_audit,
    'jarvis_analyze': jarvis_analyze,
    'jarvis_recon':   jarvis_recon,
}

def get_tools(): return TOOLS
