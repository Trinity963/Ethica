# ── Nyxt — The Browser ───────────────────────────────────────
# Slot 8 — Sovereign Browser Agent
# Keyboard-driven, Common Lisp REPL, fully scriptable.
# Portable by design — config-driven, no hard paths.
# Victory — The Architect ⟁Σ∿∞

import json
import subprocess
import socket
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / 'Ethica/config/nyxt_config.json'
PID_PATH    = Path.home() / 'Ethica/status/nyxt_pid.json'

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {
        'appimage_path': None,
        'repl_port': 4006,
        'auto_open_recon': True
    }

def _save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

def _load_pid() -> int | None:
    if PID_PATH.exists():
        try:
            return json.loads(PID_PATH.read_text()).get('pid')
        except Exception:
            pass
    return None

def _save_pid(pid: int):
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(json.dumps({'pid': pid}))

def _clear_pid():
    if PID_PATH.exists():
        PID_PATH.unlink()

def _is_running() -> bool:
    pid = _load_pid()
    if not pid:
        return False
    try:
        import os
        os.kill(pid, 0)
        return True
    except OSError:
        _clear_pid()
        return False

def _repl_available(port: int) -> bool:
    try:
        s = socket.create_connection(('127.0.0.1', port), timeout=2)
        s.close()
        return True
    except Exception:
        return False

# ── Tools ─────────────────────────────────────────────────────

def nyxt_status(args: str = '') -> str:
    cfg = _load_config()
    running = _is_running()
    pid = _load_pid()
    port = cfg.get('repl_port', 4006)
    repl = _repl_available(port) if running else False
    appimage = cfg.get('appimage_path') or 'not configured'

    lines = [
        '── Nyxt Status ─────────────────────────────',
        f'  AppImage : {appimage}',
        f'  REPL port: {port}',
        f'  Running  : {chr(9679) + " ACTIVE (PID " + str(pid) + ")" if running else "IDLE"}',
        f'  REPL     : {"available" if repl else "unavailable"}',
        f'  Auto-recon: {cfg.get("auto_open_recon", True)}',
        '─────────────────────────────────────────────',
    ]
    return chr(10).join(lines)


def nyxt_setup(args: str = '') -> str:
    args = args.strip()
    cfg = _load_config()

    if not args:
        current = cfg.get('appimage_path') or 'not set'
        return (
            'Nyxt Setup' + chr(10) +
            f'Current AppImage path: {current}' + chr(10) + chr(10) +
            'Usage: nyxt setup /path/to/Nyxt.AppImage' + chr(10) +
            'Download: https://github.com/atlas-engineer/nyxt/releases' + chr(10) + chr(10) +
            'Optional:' + chr(10) +
            '  nyxt setup port 4006       -- set REPL port' + chr(10) +
            '  nyxt setup recon on/off    -- toggle auto-open recon targets'
        )

    if args.startswith('port '):
        try:
            port = int(args.split()[1])
            cfg['repl_port'] = port
            _save_config(cfg)
            return f'✓ REPL port set to {port}'
        except Exception:
            return '✗ Invalid port number'

    if args.startswith('recon '):
        val = args.split()[1].lower()
        cfg['auto_open_recon'] = val in ('on', 'true', '1', 'yes')
        _save_config(cfg)
        return f'✓ auto_open_recon set to {cfg["auto_open_recon"]}'

    # Treat as AppImage path
    path = Path(args).expanduser()
    if not path.exists():
        return f'✗ Path not found: {path}'
    if not path.is_file():
        return f'✗ Not a file: {path}'

    try:
        result = subprocess.run(
            [str(path), '--help'],
            capture_output=True, text=True, timeout=10
        )
        cfg['appimage_path'] = str(path)
        _save_config(cfg)
        return (
            f'✓ Nyxt AppImage configured: {path}' + chr(10) +
            '✓ Config saved' + chr(10) +
            'Run: nyxt start'
        )
    except subprocess.TimeoutExpired:
        cfg['appimage_path'] = str(path)
        _save_config(cfg)
        return f'✓ Nyxt AppImage configured (smoke test timed out -- likely valid): {path}'
    except Exception as e:
        return f'✗ Could not verify AppImage: {e}'


def nyxt_open(args: str = '') -> str:
    url = args.strip()
    if not url:
        return 'Usage: nyxt open <url>'

    cfg = _load_config()
    appimage = cfg.get('appimage_path')
    if not appimage:
        return (
            '✗ Nyxt not configured.' + chr(10) +
            'Run: nyxt setup /path/to/Nyxt.AppImage'
        )

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if _is_running():
        port = cfg.get('repl_port', 4006)
        if _repl_available(port):
            result = _repl_eval(f'(nyxt:make-window :url (quri:uri "{url}"))', port)
            if result:
                return f'✓ Opened in Nyxt (REPL): {url}'

    try:
        proc = subprocess.Popen(
            [appimage, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f'✓ Nyxt launched with: {url}'
    except Exception as e:
        return f'✗ Failed to open Nyxt: {e}'


def nyxt_recon(args: str = '') -> str:
    target = args.strip()
    if not target:
        return 'Usage: nyxt recon <target>'

    if not target.startswith(('http://', 'https://')):
        target = 'https://' + target

    result = nyxt_open(target)
    if result.startswith('✓'):
        return f'✓ Recon target opened in Nyxt: {target}'
    return result


def nyxt_start(args: str = '') -> str:
    cfg = _load_config()
    appimage = cfg.get('appimage_path')

    if not appimage:
        return (
            '✗ Nyxt not configured.' + chr(10) +
            'Run: nyxt setup /path/to/Nyxt.AppImage'
        )

    if _is_running():
        pid = _load_pid()
        return f'Nyxt already running (PID {pid})'

    port = cfg.get('repl_port', 4006)

    try:
        proc = subprocess.Popen(
            [appimage, '--remote-control-port', str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        _save_pid(proc.pid)
        time.sleep(2)
        repl = _repl_available(port)
        return (
            f'✓ Nyxt started (PID {proc.pid})' + chr(10) +
            f'  REPL port: {port} -- {"available" if repl else "starting up..."}' + chr(10) +
            'Commands: nyxt eval <lisp>  |  nyxt open <url>  |  nyxt stop'
        )
    except Exception as e:
        return f'✗ Failed to start Nyxt: {e}'


def _repl_eval(expr: str, port: int) -> str | None:
    try:
        s = socket.create_connection(('127.0.0.1', port), timeout=5)
        s.sendall((expr + chr(10)).encode('utf-8'))
        time.sleep(0.5)
        response = b''
        s.settimeout(3)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        s.close()
        return response.decode('utf-8', errors='replace').strip()
    except Exception as e:
        logger.warning(f'Nyxt REPL eval failed: {e}')
        return None


def nyxt_eval(args: str = '') -> str:
    expr = args.strip()
    if not expr:
        return (
            'Usage: nyxt eval <lisp expression>' + chr(10) +
            'Example: nyxt eval (nyxt:version)'
        )

    if not _is_running():
        return '✗ Nyxt is not running. Use: nyxt start'

    cfg = _load_config()
    port = cfg.get('repl_port', 4006)

    if not _repl_available(port):
        return f'✗ REPL not available on port {port}. Nyxt may still be starting.'

    result = _repl_eval(expr, port)
    if result is None:
        return '✗ REPL eval failed -- check logs'
    return f'Nyxt REPL -> {result}' if result else '✓ Expression sent (no return value)'


def nyxt_stop(args: str = '') -> str:
    if not _is_running():
        _clear_pid()
        return 'Nyxt is not running'

    pid = _load_pid()
    try:
        import os, signal
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
            return f'✓ Nyxt stopped (SIGKILL, PID {pid})'
        except OSError:
            pass
        _clear_pid()
        return f'✓ Nyxt stopped (PID {pid})'
    except Exception as e:
        _clear_pid()
        return f'✗ Stop error (PID cleared): {e}'
