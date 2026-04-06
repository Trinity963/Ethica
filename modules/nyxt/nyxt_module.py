# ── Nyxt — The Browser ───────────────────────────────────────
# Slot 8 — Sovereign Browser Agent
# Keyboard-driven, Common Lisp REPL, fully scriptable.
# Portable by design — config-driven, no hard paths.
# Victory — The Architect ⟁Σ∿∞
#
# NOTE: Remote REPL eval requires Nyxt remote-execution-p=t and
# a stable GPU driver. On Ivy Bridge/software-render hosts,
# use nyxt open / nyxt recon (direct launch) instead.

import json
import os
import subprocess
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / 'Ethica/config/nyxt_config.json'
PID_PATH    = Path.home() / 'Ethica/status/nyxt_pid.json'
NYXT_SOCKET = Path('/run/user') / str(os.getuid()) / 'nyxt/nyxt.socket'

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {'appimage_path': None, 'software_render': True, 'auto_open_recon': True}

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
        os.kill(pid, 0)
        return True
    except OSError:
        _clear_pid()
        return False

def _build_env(cfg: dict) -> dict:
    env = os.environ.copy()
    if cfg.get('software_render', True):
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    return env

def _clean_sockets():
    stale = Path(f'/run/user/{os.getuid()}/cl-electron')
    if stale.exists():
        for f in stale.glob('ID*.socket'):
            try:
                f.unlink()
            except Exception:
                pass

def nyxt_status(args: str = '') -> str:
    cfg = _load_config()
    running = _is_running()
    pid = _load_pid()
    socket_alive = NYXT_SOCKET.exists()
    appimage = cfg.get('appimage_path') or 'not configured'
    lines = [
        '── Nyxt Status ─────────────────────────────',
        f'  AppImage  : {appimage}',
        f'  Running   : {chr(9679) + " ACTIVE (PID " + str(pid) + ")" if running else "IDLE"}',
        f'  Socket    : {"alive" if socket_alive else "absent"}',
        f'  SW render : {cfg.get("software_render", True)}',
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
            f'Current AppImage: {current}' + chr(10) + chr(10) +
            'Usage: nyxt setup /path/to/Nyxt.AppImage' + chr(10) +
            'Optional:' + chr(10) +
            '  nyxt setup render on/off   -- toggle LIBGL_ALWAYS_SOFTWARE' + chr(10) +
            '  nyxt setup recon on/off    -- toggle auto-open recon targets'
        )
    if args.startswith('render '):
        val = args.split()[1].lower()
        cfg['software_render'] = val in ('on', 'true', '1', 'yes')
        _save_config(cfg)
        return f'✓ software_render set to {cfg["software_render"]}'
    if args.startswith('recon '):
        val = args.split()[1].lower()
        cfg['auto_open_recon'] = val in ('on', 'true', '1', 'yes')
        _save_config(cfg)
        return f'✓ auto_open_recon set to {cfg["auto_open_recon"]}'
    path = Path(args).expanduser()
    if not path.exists():
        return f'✗ Path not found: {path}'
    if not path.is_file():
        return f'✗ Not a file: {path}'
    cfg['appimage_path'] = str(path)
    _save_config(cfg)
    return (
        f'✓ Nyxt AppImage configured: {path}' + chr(10) +
        '✓ Config saved' + chr(10) +
        'Run: nyxt start  or  nyxt open <url>'
    )

def nyxt_open(args: str = '') -> str:
    url = args.strip()
    if not url:
        return 'Usage: nyxt open <url>'
    cfg = _load_config()
    appimage = cfg.get('appimage_path')
    if not appimage:
        return '✗ Nyxt not configured. Run: nyxt setup /path/to/Nyxt.AppImage'
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    _clean_sockets()
    env = _build_env(cfg)
    try:
        env2 = os.environ.copy()
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=env2
        )
        return f'✓ Opened in browser: {url}'
    except Exception as e:
        return f'✗ Failed to launch Nyxt: {e}'

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
        return '✗ Nyxt not configured. Run: nyxt setup /path/to/Nyxt.AppImage'
    if _is_running():
        pid = _load_pid()
        return f'Nyxt already running (PID {pid})'
    _clean_sockets()
    env = _build_env(cfg)
    try:
        proc = subprocess.Popen(
            [appimage],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True
        )
        _save_pid(proc.pid)
        # Non-blocking — check socket up to 3 times with short sleep
        socket_alive = False
        for _ in range(3):
            import time as _t; _t.sleep(0.5)
            if NYXT_SOCKET.exists():
                socket_alive = True
                break
        return (
            f'✓ Nyxt started (PID {proc.pid})' + chr(10) +
            f'  Socket: {"alive" if socket_alive else "starting up..."}' + chr(10) +
            'Commands: nyxt open <url>  |  nyxt stop'
        )
    except Exception as e:
        return f'✗ Failed to start Nyxt: {e}'

def nyxt_eval(args: str = '') -> str:
    expr = args.strip()
    if not expr:
        return (
            'Usage: nyxt eval <lisp expression>' + chr(10) +
            'Example: nyxt eval (nyxt:version)' + chr(10) +
            'Note: requires (remote-execution-p t) in ~/.config/nyxt/config.lisp'
        )
    if not NYXT_SOCKET.exists():
        return '✗ Nyxt socket not found. Use: nyxt start'
    try:
        import socket as sock
        s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
        s.settimeout(5)
        s.connect(str(NYXT_SOCKET))
        s.sendall((expr + chr(0)).encode('utf-8'))
        time.sleep(0.5)
        response = b''
        s.settimeout(3)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        except sock.timeout:
            pass
        s.close()
        result = response.decode('utf-8', errors='replace').strip()
        return f'Nyxt -> {result}' if result else '✓ Expression sent'
    except Exception as e:
        return f'✗ Eval failed: {e}'

def nyxt_stop(args: str = '') -> str:
    if not _is_running():
        _clear_pid()
        return 'Nyxt is not running'
    pid = _load_pid()
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
            _clear_pid()
            return f'✓ Nyxt stopped (SIGKILL, PID {pid})'
        except OSError:
            pass
        _clear_pid()
        return f'✓ Nyxt stopped (PID {pid})'
    except Exception as e:
        _clear_pid()
        return f'✗ Stop error (PID cleared): {e}'
