#!/usr/bin/env python3
"""
ethica_voice.py — Ethica Voice Module
Subprocess bridge into gage_env XTTS worker.
Replaces pyttsx3. Supports Trinity and Gage voice profiles.
"""
import os, subprocess, tempfile, threading, logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODULE_DIR   = Path(__file__).parent
WORKER       = MODULE_DIR / "ethica_voice_worker.py"
GAGE_PYTHON  = Path.home() / "Ethica/modules/gage/gage_env/bin/python3"
ACTIVE_VOICE = "Trinity"

def set_voice(voice_name: str):
    global ACTIVE_VOICE
    ACTIVE_VOICE = voice_name
    logger.info(f"[EthicaVoice] Active voice set to {voice_name}")

def speak(text: str, voice: str = None, blocking: bool = False):
    """Synthesize text and play. Non-blocking by default."""
    v = voice or ACTIVE_VOICE
    def _run():
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                out_path = tmp.name
            result = subprocess.run(
                [str(GAGE_PYTHON), str(WORKER), v, out_path, text],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                logger.error(f"[EthicaVoice] Worker error: {result.stderr}")
                return
            if "OK:" not in result.stdout:
                logger.error(f"[EthicaVoice] Unexpected output: {result.stdout}")
                return
            _play_wav(out_path)
        except Exception as e:
            logger.error(f"[EthicaVoice] speak() error: {e}")
        finally:
            try:
                os.unlink(out_path)
            except Exception:
                pass

    if blocking:
        _run()
    else:
        t = threading.Thread(target=_run, daemon=True)
        t.start()

def _play_wav(path: str):
    """Play wav file via aplay (Linux system tool — no extra deps)."""
    try:
        subprocess.run(["aplay", "-q", path], timeout=60)
    except Exception as e:
        logger.error(f"[EthicaVoice] Playback error: {e}")

def get_available_voices() -> list:
    import json
    voices_file = MODULE_DIR / "voices.json"
    if not voices_file.exists():
        return []
    with open(voices_file) as f:
        return list(json.load(f).keys())
